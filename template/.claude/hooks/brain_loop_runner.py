"""brain_loop_runner — opt-in Stop hook that surfaces due loops.

Fires when Claude Code finishes a response. Reads WORKSPACE_LOOPS.md,
identifies any loops whose `Next run` date is on/before today, and
emits a one-line directive to stdout (which Claude treats as a system
nudge).

Refuses to:
- Run any observation commands directly (the slash command /loop-run
  does that, with user awareness).
- Invent run results, dates, or status.
- Fire more than once per session for the same set of due loops (uses
  a tiny .claude/.loops-runner-state file to dedupe within a session).

Opt in by adding to .claude/settings.json:
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command",
           "command": "python .claude/hooks/brain_loop_runner.py",
           "timeout": 5}
        ]
      }
    ]

Configuration (env vars):
    LOOPS_FILE         Path relative to project root. Default: WORKSPACE_LOOPS.md
    LOOPS_QUIET_HOURS  If set to integer N, don't re-emit within N hours of
                       the previous emission. Default: 6.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOOPS_FILENAME = os.environ.get("LOOPS_FILE", "WORKSPACE_LOOPS.md")
QUIET_HOURS = int(os.environ.get("LOOPS_QUIET_HOURS", "6"))
STATE_FILENAME = os.path.join(".claude", ".loops-runner-state")

loops_path = os.path.join(os.getcwd(), LOOPS_FILENAME)
state_path = os.path.join(os.getcwd(), STATE_FILENAME)

if not os.path.exists(loops_path):
    sys.exit(0)

# Quiet-hours check: if we emitted recently, stay silent.
try:
    if os.path.exists(state_path):
        last = os.path.getmtime(state_path)
        if (datetime.now().timestamp() - last) < QUIET_HOURS * 3600:
            sys.exit(0)
except Exception:
    pass

try:
    text = open(loops_path, encoding="utf-8").read()
except Exception:
    sys.exit(0)

# Parse loops: each ## LOOP: <slug> section, find Status + Next run.
# We intentionally keep parsing dumb-and-grep-shaped so the schema can
# evolve without breaking the runner.
LOOP_HEADER = re.compile(r"^##\s+LOOP:\s+(\S+)\s*$", re.MULTILINE)
NEXT_RUN = re.compile(r"^-\s+\*\*Next run\*\*:\s+(\S+)", re.MULTILINE)
STATUS = re.compile(r"^-\s+\*\*Status\*\*:\s+(\S+)", re.MULTILINE)
GOAL = re.compile(r"^-\s+\*\*Goal\*\*:\s+(.+?)$", re.MULTILINE)

slugs = list(LOOP_HEADER.finditer(text))
if not slugs:
    sys.exit(0)

today = datetime.now(timezone.utc).date()
due: list[tuple[str, str]] = []  # (slug, goal)

for i, m in enumerate(slugs):
    slug = m.group(1)
    section_end = slugs[i + 1].start() if i + 1 < len(slugs) else len(text)
    section = text[m.end() : section_end]

    status_m = STATUS.search(section)
    status = status_m.group(1).lower() if status_m else "active"
    if status in ("paused", "retired"):
        continue

    nr_m = NEXT_RUN.search(section)
    if not nr_m:
        continue
    nr_val = nr_m.group(1).strip().rstrip(".")
    # `manual` triggers never auto-fire.
    if nr_val.lower() in ("manual", "—", "tbd"):
        continue
    try:
        nr_date = datetime.strptime(nr_val, "%Y-%m-%d").date()
    except ValueError:
        continue
    if nr_date <= today:
        goal_m = GOAL.search(section)
        goal = goal_m.group(1).strip() if goal_m else "(no goal)"
        # Truncate long goals so the directive stays one line each.
        if len(goal) > 80:
            goal = goal[:77] + "..."
        due.append((slug, goal))

if not due:
    sys.exit(0)

# Emit the directive. Keep it terse — Stop hooks fire often and we don't
# want to spam every turn.
print("")
print("## ===== LOOPS DUE =====")
print("")
print(f"{len(due)} self-improving loop(s) in {LOOPS_FILENAME} are at or past their")
print("Next run date. Each can be run, tuned, or paused. Loops won't fire")
print("themselves — surfacing them is this hook's only job.")
print("")
for slug, goal in due:
    print(f"  - **{slug}** — {goal}")
print("")
print(f"Actions: /loop-run <slug> · /loop-tune <slug> · /loop  (status overview)")
print(f"Silence this for {QUIET_HOURS}h: nothing — touching this file does it automatically")
print(f"once you act on a loop. Re-emit on Stop after the quiet window expires.")
print("")
print("## ===== END LOOPS DUE =====")

# Mark state so we don't re-emit during the quiet window.
try:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        f.write(datetime.now(timezone.utc).isoformat() + "\n")
        for slug, _ in due:
            f.write(slug + "\n")
except Exception:
    # State write is best-effort; don't fail the hook.
    pass
