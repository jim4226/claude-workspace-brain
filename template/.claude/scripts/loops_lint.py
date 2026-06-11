"""loops_lint — static quality scorer for WORKSPACE_LOOPS.md.

Run:
    python .claude/scripts/loops_lint.py [path-to-WORKSPACE_LOOPS.md]

Scores six axes (total 100):
    Required fields per loop       (25 pts)
    History append-only hygiene    (15 pts)
    Tuning Log rationale (Reason:) (20 pts)
    Trigger sanity                 (15 pts)
    Stale Next-run                 (15 pts)
    Status consistency             (10 pts)

Emits a score plus a prioritized list of findings (ERROR / WARN / INFO /
OK). Always exits 0 — advisory, never a build blocker, mirroring
brain_lint.py.

No third-party deps; stdlib only. Python 3.8+.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Tuple

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_FILE = "WORKSPACE_LOOPS.md"

REQUIRED_FIELDS = [
    "Goal",
    "Trigger",
    "Next run",
    "Observation",
    "Criterion",
    "Status",
]
RECOMMENDED_FIELDS = ["Brain context", "First-failure action"]

REASON_PATTERN = re.compile(
    r"\b(reason|because|driven by|motivat\w+)\b", re.IGNORECASE
)
HISTORY_DATE_PATTERN = re.compile(r"^\s*-\s+\d{4}-\d{2}-\d{2}\s+(SUCCESS|FAILURE|SKIPPED)\b")
VALID_STATUS = {"active", "stable", "paused", "retired"}
TRIGGER_OK_PATTERNS = [
    re.compile(r"^every\s+\d+d$", re.IGNORECASE),
    re.compile(r"^manual$", re.IGNORECASE),
    re.compile(r"^on-session-start$", re.IGNORECASE),
]

STALE_NEXTRUN_DAYS = 60


@dataclass
class Loop:
    slug: str
    start_line: int
    body: str
    history_body: str = ""
    tuning_body: str = ""

    def field(self, name: str) -> str | None:
        m = re.search(
            rf"^-\s+\*\*{re.escape(name)}\*\*:\s*(.+?)\s*$",
            self.body,
            re.MULTILINE,
        )
        return m.group(1) if m else None


@dataclass
class Finding:
    severity: str  # ERROR / WARN / INFO / OK
    msg: str
    points_lost: float = 0.0


SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2, "OK": 3}


def parse_loops(text: str) -> List[Loop]:
    loops: List[Loop] = []
    headers = list(re.finditer(r"^##\s+LOOP:\s+(\S+)\s*$", text, re.MULTILINE))
    for i, m in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[m.end():end]
        # Split out the History and Tuning Log subsections
        history = ""
        tuning = ""
        hist_m = re.search(r"^###\s+History\s*$", section, re.MULTILINE)
        tune_m = re.search(r"^###\s+Tuning Log\s*$", section, re.MULTILINE)
        if hist_m:
            hist_end = tune_m.start() if tune_m and tune_m.start() > hist_m.end() else len(section)
            history = section[hist_m.end():hist_end]
        if tune_m:
            tuning = section[tune_m.end():]
        # The "body" of the spec excludes History/Tuning subsections
        body_end = hist_m.start() if hist_m else (tune_m.start() if tune_m else len(section))
        body = section[:body_end]
        loops.append(
            Loop(
                slug=m.group(1),
                start_line=text[: m.start()].count("\n") + 1,
                body=body,
                history_body=history,
                tuning_body=tuning,
            )
        )
    return loops


# ---------- per-axis scorers -----------------------------------------------


def score_required_fields(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 25
    if not loops:
        return max_pts, [Finding("INFO", "No loops defined yet (file may be a fresh template).")]
    findings: List[Finding] = []
    missing_total = 0
    for loop in loops:
        missing = [f for f in REQUIRED_FIELDS if loop.field(f) is None]
        if missing:
            missing_total += len(missing)
            findings.append(
                Finding(
                    "ERROR" if len(missing) >= 3 else "WARN",
                    f"Loop '{loop.slug}' missing fields: {', '.join(missing)}.",
                )
            )
    if missing_total == 0:
        return max_pts, [Finding("OK", f"All loops ({len(loops)}) have the {len(REQUIRED_FIELDS)} required fields.")]
    # 4 points per missing field, capped at max_pts
    lost = min(max_pts, missing_total * 4)
    for f in findings:
        # Distribute points proportionally (cosmetic; report shows the total)
        f.points_lost = lost / len(findings)
    return max_pts - lost, findings


def score_history_hygiene(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 15
    if not loops:
        return max_pts, [Finding("INFO", "No loops to lint History on.")]
    findings: List[Finding] = []
    total_lines = 0
    bad_lines = 0
    for loop in loops:
        for raw in loop.history_body.splitlines():
            line = raw.strip()
            if not line or not line.startswith("-"):
                continue
            total_lines += 1
            if not HISTORY_DATE_PATTERN.match(raw):
                bad_lines += 1
                findings.append(
                    Finding(
                        "WARN",
                        f"Loop '{loop.slug}' History entry malformed (need 'YYYY-MM-DD SUCCESS|FAILURE|SKIPPED'): {line[:60]}",
                    )
                )
    if total_lines == 0:
        return max_pts, [Finding("INFO", "No History entries yet — fresh loops.")]
    if bad_lines == 0:
        return max_pts, [Finding("OK", f"All {total_lines} History entries well-formed.")]
    ratio_bad = bad_lines / total_lines
    pts = max_pts * (1 - ratio_bad)
    lost = max_pts - pts
    for f in findings[:5]:  # cap noise
        f.points_lost = lost / max(1, len(findings))
    return pts, findings[:5]


def score_tuning_rationale(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 20
    if not loops:
        return max_pts, [Finding("INFO", "No loops to lint Tuning Log on.")]
    findings: List[Finding] = []
    total = 0
    with_reason = 0
    for loop in loops:
        for raw in loop.tuning_body.splitlines():
            line = raw.strip()
            if not line or not line.startswith("-"):
                continue
            total += 1
            if REASON_PATTERN.search(line):
                with_reason += 1
            else:
                findings.append(
                    Finding(
                        "WARN",
                        f"Loop '{loop.slug}' Tuning entry missing 'Reason:' clause: {line[:60]}",
                    )
                )
    if total == 0:
        return max_pts, [Finding("INFO", "No Tuning Log entries yet.")]
    ratio = with_reason / total
    if ratio >= 0.85:
        return max_pts, [Finding("OK", f"{with_reason}/{total} Tuning entries include rationale.")]
    pts = max_pts * ratio
    lost = max_pts - pts
    for f in findings[:5]:
        f.points_lost = lost / max(1, len(findings))
    return pts, findings[:5]


def score_trigger_sanity(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 15
    if not loops:
        return max_pts, []
    findings: List[Finding] = []
    bad = 0
    for loop in loops:
        trigger = loop.field("Trigger")
        if trigger is None:
            continue  # missing-field axis catches this
        clean = trigger.strip().rstrip(".")
        if not any(p.match(clean) for p in TRIGGER_OK_PATTERNS):
            bad += 1
            findings.append(
                Finding(
                    "WARN",
                    f"Loop '{loop.slug}' has unrecognized Trigger '{clean}' — expected 'every Nd', 'manual', or 'on-session-start'.",
                )
            )
    if bad == 0:
        return max_pts, [Finding("OK", "All Triggers parse.")]
    ratio_bad = bad / len(loops)
    pts = max_pts * (1 - ratio_bad)
    lost = max_pts - pts
    for f in findings:
        f.points_lost = lost / max(1, len(findings))
    return pts, findings


def score_stale_nextrun(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 15
    if not loops:
        return max_pts, []
    today = datetime.now(timezone.utc).date()
    findings: List[Finding] = []
    stale = 0
    eligible = 0
    for loop in loops:
        status = (loop.field("Status") or "active").strip().lower().rstrip(".")
        if status not in ("active", "stable"):
            continue
        eligible += 1
        nr = loop.field("Next run")
        if nr is None:
            continue
        nr_clean = nr.strip().rstrip(".")
        if nr_clean.lower() in ("manual", "—", "tbd", ""):
            continue
        try:
            nr_date = datetime.strptime(nr_clean, "%Y-%m-%d").date()
        except ValueError:
            findings.append(
                Finding("WARN", f"Loop '{loop.slug}' Next run '{nr_clean}' not parseable as YYYY-MM-DD.")
            )
            continue
        age = (today - nr_date).days
        if age > STALE_NEXTRUN_DAYS:
            stale += 1
            findings.append(
                Finding(
                    "WARN",
                    f"Loop '{loop.slug}' Next run was {age}d ago — overdue or abandoned. Run, tune, or pause.",
                )
            )
    if eligible == 0:
        return max_pts, [Finding("INFO", "No active/stable loops to check freshness on.")]
    if not findings:
        return max_pts, [Finding("OK", f"All {eligible} active/stable loops have fresh or future Next-run dates.")]
    ratio_stale = stale / eligible
    pts = max_pts * (1 - ratio_stale)
    lost = max_pts - pts
    for f in findings:
        f.points_lost = lost / max(1, len(findings))
    return pts, findings


def score_status_consistency(loops: List[Loop]) -> Tuple[float, List[Finding]]:
    max_pts = 10
    if not loops:
        return max_pts, []
    findings: List[Finding] = []
    bad = 0
    for loop in loops:
        status = loop.field("Status")
        if status is None:
            continue  # required-fields axis catches this
        clean = status.strip().lower().rstrip(".")
        if clean not in VALID_STATUS:
            bad += 1
            findings.append(
                Finding(
                    "WARN",
                    f"Loop '{loop.slug}' Status '{clean}' not in {sorted(VALID_STATUS)}.",
                )
            )
    if bad == 0:
        return max_pts, [Finding("OK", f"All Status values are valid ({len(loops)} loops).")]
    ratio_bad = bad / len(loops)
    pts = max_pts * (1 - ratio_bad)
    lost = max_pts - pts
    for f in findings:
        f.points_lost = lost / max(1, len(findings))
    return pts, findings


# ---------- main -----------------------------------------------------------


def lint(file_path: str) -> int:
    if not os.path.exists(file_path):
        print(f"loops_lint: file not found: {file_path}")
        print("(Run /loop-init or /loop-suggest to create your first loop.)")
        return 0
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    loops = parse_loops(text)
    kb = len(text.encode("utf-8")) / 1024

    scorers = [
        ("Required fields", lambda: score_required_fields(loops)),
        ("History hygiene", lambda: score_history_hygiene(loops)),
        ("Tuning rationale", lambda: score_tuning_rationale(loops)),
        ("Trigger sanity", lambda: score_trigger_sanity(loops)),
        ("Stale Next-run", lambda: score_stale_nextrun(loops)),
        ("Status consistency", lambda: score_status_consistency(loops)),
    ]
    weights = {
        "Required fields": 25,
        "History hygiene": 15,
        "Tuning rationale": 20,
        "Trigger sanity": 15,
        "Stale Next-run": 15,
        "Status consistency": 10,
    }

    total = 0.0
    all_findings: List[Tuple[str, Finding]] = []
    breakdown: List[Tuple[str, float, float]] = []
    for axis, fn in scorers:
        pts, findings = fn()
        breakdown.append((axis, pts, weights[axis]))
        total += pts
        for f in findings:
            all_findings.append((axis, f))

    all_findings.sort(key=lambda x: SEVERITY_ORDER.get(x[1].severity, 9))

    print("loops_lint v1.0")
    print(f"File: {file_path} ({len(text.splitlines())} lines, {kb:.1f} KB, {len(loops)} loops)")
    print("")
    print(f"Score: {total:.0f}/100")
    print("")
    print("Breakdown:")
    for axis, pts, weight in breakdown:
        bar_filled = int(round(20 * pts / weight)) if weight else 0
        bar = "#" * bar_filled + "." * (20 - bar_filled)
        print(f"  [{bar}] {axis:<22} {pts:5.1f} / {weight}")
    print("")
    if not all_findings:
        print("No findings.")
    else:
        print("Findings (most severe first):")
        for axis, f in all_findings[:20]:
            tag = f"[{f.severity}]".ljust(8)
            loss = f" (~{f.points_lost:.1f} pts)" if f.points_lost > 0 else ""
            print(f"  {tag} {axis}: {f.msg}{loss}")
        if len(all_findings) > 20:
            print(f"  ... and {len(all_findings) - 20} more (showing top 20)")
    print("")
    print("Run /loop-suggest to propose new loops, /loop-tune <slug> to refine existing ones.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    sys.exit(lint(path))
