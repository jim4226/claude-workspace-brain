"""brain_loop_autopilot — opt-in Stop hook that DRIVES due loops.

This is the "run continuously" half of self-improving loops. The
companion `brain_loop_runner.py` only SURFACES due loops; this one
BLOCKS the stop and asks Claude to execute one. Loops with a `Next run`
on or before today get an `/loop-run <slug>` directive; Claude runs the
loop, appends a History entry, the History grows, and the next Stop
event re-evaluates.

Self-improvement still happens via /loop-run's existing rules:
- 3+ consecutive FAILUREs prepend a `Reconsidering …` entry to the
  brain's OPEN QUESTIONS (no auto-tuning).
- 5+ consecutive SUCCESSes auto-promote Status to `stable`.
- All spec changes require /loop-tune with user approval.

Safety, in order of how the hook decides whether to block:

  1. KILL SWITCH       BRAIN_LOOPS_OFF=1                always allows stop
  2. SESSION BUDGET    BRAIN_LOOP_MAX_PER_SESSION       blocks per session
                       default: 2
  3. PER-LOOP BUDGET   BRAIN_LOOP_MAX_PER_LOOP          per-loop runs/session
                       default: 1
  4. ANTI-SPIN         History entry count must INCREASE between blocks
                       for the same loop in the same session, else allow stop.
                       Cannot be disabled.
  5. STATUS GATE       Status must be `active` or `stable`. `paused`/`retired`
                       loops are never driven.
  6. SCHEMA GATE       Next run must parse as YYYY-MM-DD. `manual`/`—`/`tbd`
                       Next-run values never auto-fire.

Any exception => allow the stop. Safety failure mode is "do nothing".

Session state lives in tempdir, keyed by SHA-1(cwd) — never written into
the repo. Expires after 7 days.

Enable with `python _install.py --with-loop-autopilot` (or hand-edit
.claude/settings.json to add the Stop block — same shape as the
runner's).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOOPS_FILENAME = os.environ.get("LOOPS_FILE", "WORKSPACE_LOOPS.md")
MAX_PER_SESSION = int(os.environ.get("BRAIN_LOOP_MAX_PER_SESSION", "2"))
MAX_PER_LOOP = int(os.environ.get("BRAIN_LOOP_MAX_PER_LOOP", "1"))
STATE_TTL_SEC = 7 * 24 * 3600

LOOP_HEADER = re.compile(r"^##\s+LOOP:\s+(\S+)\s*$", re.MULTILINE)
NEXT_RUN = re.compile(r"^-\s+\*\*Next run\*\*:\s+(\S+)", re.MULTILINE)
STATUS = re.compile(r"^-\s+\*\*Status\*\*:\s+(\S+)", re.MULTILINE)
GOAL = re.compile(r"^-\s+\*\*Goal\*\*:\s+(.+?)$", re.MULTILINE)
HISTORY_HEADER = re.compile(r"^###\s+History\s*$", re.MULTILINE)
HISTORY_ENTRY = re.compile(r"^-\s+\d{4}-\d{2}-\d{2}\s+(SUCCESS|FAILURE|SKIPPED)\b",
                           re.MULTILINE)


def state_path() -> str:
    digest = hashlib.sha1(os.getcwd().encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(tempfile.gettempdir(), f"brain_loop_autopilot_{digest}.json")


def load_state() -> dict:
    try:
        with open(state_path(), "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        return {}
    now = time.time()
    return {
        k: v
        for k, v in state.items()
        if isinstance(v, dict) and now - v.get("ts", 0) < STATE_TTL_SEC
    }


def save_state(state: dict) -> None:
    try:
        with open(state_path(), "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        # State write is best-effort; failure must not break the hook.
        pass


def count_history(section: str) -> int:
    """Number of dated History entries in one loop's section.

    Counted on every Stop; if this number didn't go up since the last
    block, the loop didn't actually run — anti-spin trips."""
    hh = HISTORY_HEADER.search(section)
    body = section[hh.end():] if hh else section
    return len(HISTORY_ENTRY.findall(body))


def pick_due_loop(text: str, sess: dict) -> tuple[str, str, int] | None:
    """Return (slug, goal, history_count) of the first eligible due loop,
    or None. Eligible = active|stable, Next run <= today, under budgets,
    anti-spin OK."""
    today = datetime.now(timezone.utc).date()
    headers = list(LOOP_HEADER.finditer(text))
    for i, m in enumerate(headers):
        slug = m.group(1)
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[m.end():end]

        st = STATUS.search(section)
        status = (st.group(1).lower().strip(".") if st else "active")
        if status not in ("active", "stable"):
            continue

        nr = NEXT_RUN.search(section)
        if not nr:
            continue
        nr_val = nr.group(1).strip().rstrip(".")
        if nr_val.lower() in ("manual", "—", "tbd", ""):
            continue
        try:
            nr_date = datetime.strptime(nr_val, "%Y-%m-%d").date()
        except ValueError:
            continue
        if nr_date > today:
            continue

        # Per-loop budget for this session
        runs = sess["runs"].get(slug, 0)
        if runs >= MAX_PER_LOOP:
            continue

        # Anti-spin: if we already blocked for this loop this session and
        # history hasn't grown since, the loop didn't actually run — bail.
        history_count = count_history(section)
        seen = sess["seen"].get(slug)
        if seen is not None and history_count <= seen:
            print(
                f"brain_loop_autopilot: loop {slug!r} produced no new "
                f"History entry since last block (count={history_count}). "
                f"Allowing stop to avoid spin.",
                file=sys.stderr,
            )
            return None

        goal = GOAL.search(section)
        return slug, (goal.group(1).strip() if goal else "(no goal)"), history_count

    return None


def build_directive(slug: str, goal: str, sess_runs: int, sess_blocks: int) -> str:
    """The text Claude sees when the stop is blocked. Mirrors the LOOPS
    DUE wording style so it reads like part of the same family."""
    return (
        "## ===== LOOP AUTOPILOT — DRIVING ONE LOOP =====\n"
        "\n"
        f"Loop `{slug}` is due today and within autopilot budget "
        f"(session blocks {sess_blocks}/{MAX_PER_SESSION}, "
        f"this-loop runs {sess_runs + 1}/{MAX_PER_LOOP}).\n"
        f"Goal: {goal}\n"
        "\n"
        f"Execute exactly **one** iteration now: invoke `/loop-run {slug}`,\n"
        "following the slash command's contract:\n"
        "  - run the loop's Observation,\n"
        "  - evaluate the Criterion against the parsed value,\n"
        "  - APPEND one History entry (date · STATUS · snippet → action),\n"
        "  - update Next run per the Trigger,\n"
        "  - escalate to OPEN QUESTIONS if this is a 3+ FAILURE streak,\n"
        "  - promote to `stable` if this is a 5+ SUCCESS streak.\n"
        "\n"
        "Do NOT invent the observation output. If the observation can't run\n"
        "(missing dependency, permission, manual: prompt with no user), the\n"
        "run is SKIPPED. Then finish your reply — the autopilot's anti-spin\n"
        "guard will allow the stop on the next event if History didn't grow.\n"
        "\n"
        "Kill switches: `BRAIN_LOOPS_OFF=1` env var, or set the loop's Status\n"
        "to `paused`/`retired` via `/loop-tune` to stop autopilot for it.\n"
        "\n"
        "## ===== END AUTOPILOT DIRECTIVE ====="
    )


def main() -> int:
    if os.environ.get("BRAIN_LOOPS_OFF"):
        return 0

    # Session id from the Stop hook payload — keys our state file.
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        payload = {}
    session = str(payload.get("session_id") or "default")

    loops_path = os.path.join(os.getcwd(), LOOPS_FILENAME)
    if not os.path.exists(loops_path):
        return 0
    try:
        text = open(loops_path, encoding="utf-8").read()
    except Exception:
        return 0

    state = load_state()
    sess = state.get(session) or {
        "ts": time.time(),
        "blocks": 0,
        "runs": {},
        "seen": {},
    }

    # Hard session-wide cap.
    if sess["blocks"] >= MAX_PER_SESSION:
        return 0

    pick = pick_due_loop(text, sess)
    if pick is None:
        return 0
    slug, goal, history_count = pick

    sess["ts"] = time.time()
    sess["blocks"] += 1
    sess["runs"][slug] = sess["runs"].get(slug, 0) + 1
    sess["seen"][slug] = history_count
    state[session] = sess
    save_state(state)

    # Emit the Stop-hook block decision. Claude Code's Stop hook reads a
    # JSON object on stdout with shape:
    #   {"decision": "block", "reason": "<text shown to Claude>"}
    print(json.dumps({
        "decision": "block",
        "reason": build_directive(slug, goal, sess["runs"][slug] - 1, sess["blocks"]),
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Catastrophic failure must NEVER break the session. Allowing the
        # stop is the safe failure mode.
        print(f"brain_loop_autopilot: unexpected error: {e} (allowing stop)",
              file=sys.stderr)
        sys.exit(0)
