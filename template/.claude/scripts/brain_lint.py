"""brain_lint - static quality scorer for WORKSPACE_BRAIN.md.

Run:
    python .claude/scripts/brain_lint.py [path-to-brain.md]

Scores six axes (total 100):
    Required sections      (20 pts)
    Size budget            (20 pts)
    Header freshness       (20 pts)
    Section balance        (15 pts)
    Decision rationale     (15 pts)
    Thread hygiene         (10 pts)

Emits a score plus a prioritized list of findings (ERROR / WARN / INFO / OK).
Always exits 0 - the linter is advisory, never a build blocker.

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

# Reconfigure stdout to UTF-8 so emojis in section titles survive on
# Windows consoles (cp1252 by default). No-op on macOS/Linux.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------- configuration --------------------------------------------------

DEFAULT_FILE = "WORKSPACE_BRAIN.md"

# Section names we expect. Match is approximate (case-insensitive, ignores
# leading emoji/whitespace), so renaming "ACTIVE FOCUS" to "Focus" still passes.
REQUIRED_SECTIONS = [
    "ACTIVE FOCUS",
    "ACTIVE THREADS",
    "DECISIONS LOG",
    "SYNAPSES",
    "KEY NUMBERS",
    "RECENT SESSIONS",
    "OPEN QUESTIONS",
]

SIZE_BUDGET_KB = 32          # injected size cap
SIZE_SOFT_KB = 16            # soft target
FRESHNESS_OK_DAYS = 14       # last-sync date should be within
FRESHNESS_STALE_DAYS = 45    # beyond this, lose all freshness points
MAX_DOMINANT_SHARE = 0.40    # no section should exceed this % of total
MAX_RECENT_SESSIONS = 10
DECISION_REASON_PATTERNS = re.compile(
    r"\b(reason|why|because|driven by|motivat\w+)\b", re.IGNORECASE
)

# ---------- data model -----------------------------------------------------


@dataclass
class Section:
    title: str
    body: str
    start_line: int


@dataclass
class Finding:
    severity: str  # "ERROR" / "WARN" / "INFO" / "OK"
    msg: str
    points_lost: float = 0.0


SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2, "OK": 3}


# ---------- helpers --------------------------------------------------------


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def normalize_section_title(s: str) -> str:
    s = re.sub(r"[^\w\s]", "", s)        # drop emojis / punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s.upper()


def parse_sections(text: str) -> List[Section]:
    sections: List[Section] = []
    current_title: str | None = None
    current_body: List[str] = []
    current_start = 0
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_title is not None:
                sections.append(
                    Section(
                        title=current_title,
                        body="\n".join(current_body),
                        start_line=current_start,
                    )
                )
            current_title = m.group(1).strip()
            current_body = []
            current_start = i
        elif current_title is not None:
            current_body.append(line)
    if current_title is not None:
        sections.append(
            Section(
                title=current_title,
                body="\n".join(current_body),
                start_line=current_start,
            )
        )
    return sections


def find_section(sections: List[Section], wanted: str) -> Section | None:
    wanted_n = normalize_section_title(wanted)
    for s in sections:
        if wanted_n in normalize_section_title(s.title):
            return s
    return None


def parse_last_sync(text: str) -> datetime | None:
    m = re.search(r"Last sync:\s*(\d{4}-\d{2}-\d{2})", text)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------- per-axis scorers ------------------------------------------------


def score_required_sections(sections: List[Section]) -> Tuple[float, List[Finding]]:
    max_pts = 20
    findings: List[Finding] = []
    missing = [s for s in REQUIRED_SECTIONS if find_section(sections, s) is None]
    if not missing:
        return max_pts, [Finding("OK", "All 7 required sections present.")]
    pts = max(0, max_pts - 3 * len(missing))
    findings.append(
        Finding(
            "WARN" if len(missing) <= 2 else "ERROR",
            f"Missing required sections: {', '.join(missing)}.",
            points_lost=max_pts - pts,
        )
    )
    return pts, findings


def score_size(text: str) -> Tuple[float, List[Finding]]:
    max_pts = 20
    findings: List[Finding] = []
    kb = len(text.encode("utf-8")) / 1024
    if kb <= SIZE_SOFT_KB:
        return max_pts, [Finding("OK", f"File size {kb:.1f}KB (soft target <={SIZE_SOFT_KB}KB).")]
    if kb >= SIZE_BUDGET_KB:
        findings.append(
            Finding(
                "ERROR",
                f"File size {kb:.1f}KB exceeds injection cap {SIZE_BUDGET_KB}KB. "
                "Archive oldest sessions / decisions to WORKSPACE_BRAIN_ARCHIVE.md.",
                points_lost=max_pts,
            )
        )
        return 0, findings
    # linear interp between soft and hard caps
    pts = max_pts * (SIZE_BUDGET_KB - kb) / (SIZE_BUDGET_KB - SIZE_SOFT_KB)
    findings.append(
        Finding(
            "WARN",
            f"File size {kb:.1f}KB exceeds soft target ({SIZE_SOFT_KB}KB). "
            "Consider archiving older entries.",
            points_lost=max_pts - pts,
        )
    )
    return pts, findings


def score_freshness(text: str, file_path: str) -> Tuple[float, List[Finding]]:
    max_pts = 20
    findings: List[Finding] = []
    declared = parse_last_sync(text)
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
    reference = declared or mtime
    age_days = (datetime.now(timezone.utc) - reference).days
    label = "Last sync date" if declared else "file mtime (no Last sync header)"
    if age_days <= FRESHNESS_OK_DAYS:
        return max_pts, [Finding("OK", f"{label} is {age_days}d old (fresh).")]
    if age_days >= FRESHNESS_STALE_DAYS:
        findings.append(
            Finding(
                "WARN",
                f"{label} is {age_days}d old (>={FRESHNESS_STALE_DAYS}d). "
                "Brain may be drifting from reality.",
                points_lost=max_pts,
            )
        )
        return 0, findings
    # linear decay
    pts = max_pts * (FRESHNESS_STALE_DAYS - age_days) / (FRESHNESS_STALE_DAYS - FRESHNESS_OK_DAYS)
    findings.append(
        Finding(
            "INFO",
            f"{label} is {age_days}d old (target <={FRESHNESS_OK_DAYS}d).",
            points_lost=max_pts - pts,
        )
    )
    return pts, findings


def score_balance(sections: List[Section]) -> Tuple[float, List[Finding]]:
    max_pts = 15
    findings: List[Finding] = []
    sizes = [(s.title, len(strip_html_comments(s.body).strip())) for s in sections]
    total = sum(sz for _, sz in sizes) or 1
    dominant = max(sizes, key=lambda x: x[1], default=("", 0))
    share = dominant[1] / total
    if share <= MAX_DOMINANT_SHARE:
        return max_pts, [Finding("OK", f"Section balance OK (largest = {dominant[0]} at {share*100:.0f}%).")]
    pts = max(0, max_pts * (1 - (share - MAX_DOMINANT_SHARE) / (1 - MAX_DOMINANT_SHARE)))
    findings.append(
        Finding(
            "WARN",
            f"Section '{dominant[0]}' is {share*100:.0f}% of file - consider splitting or archiving.",
            points_lost=max_pts - pts,
        )
    )
    return pts, findings


def score_decision_rationale(sections: List[Section]) -> Tuple[float, List[Finding]]:
    max_pts = 15
    findings: List[Finding] = []
    decisions = find_section(sections, "DECISIONS LOG")
    if not decisions:
        return 0, [Finding("WARN", "No DECISIONS LOG section found - can't grade rationale.", points_lost=max_pts)]
    body = strip_html_comments(decisions.body)
    entries = [ln for ln in body.splitlines() if re.match(r"^\s*-\s+", ln)]
    if not entries:
        return max_pts, [Finding("INFO", "DECISIONS LOG is empty - nothing to grade.")]
    with_reason = sum(1 for e in entries if DECISION_REASON_PATTERNS.search(e))
    ratio = with_reason / len(entries)
    pts = max_pts * ratio
    if ratio >= 0.85:
        sev, label = "OK", f"{with_reason}/{len(entries)} decisions include rationale."
    elif ratio >= 0.5:
        sev, label = "WARN", f"Only {with_reason}/{len(entries)} decisions include rationale (target >=85%)."
    else:
        sev, label = "ERROR", f"Only {with_reason}/{len(entries)} decisions include rationale. Add 'Reason:' to each entry."
    findings.append(Finding(sev, label, points_lost=max_pts - pts))
    return pts, findings


def score_thread_hygiene(sections: List[Section]) -> Tuple[float, List[Finding]]:
    max_pts = 10
    findings: List[Finding] = []
    threads = find_section(sections, "ACTIVE THREADS")
    if not threads:
        return 0, [Finding("WARN", "No ACTIVE THREADS section found.", points_lost=max_pts)]
    body = strip_html_comments(threads.body)
    entries = [ln for ln in body.splitlines() if re.match(r"^\s*-\s+", ln)]
    if not entries:
        return max_pts, [Finding("INFO", "ACTIVE THREADS is empty.")]
    done_markers = re.compile(r"(\(done\)|done\b|✅|\[x\]|completed)", re.IGNORECASE)
    done = sum(1 for e in entries if done_markers.search(e))
    active = len(entries) - done
    if done > active * 2 and done >= 5:
        pts = max_pts * 0.5
        findings.append(
            Finding(
                "WARN",
                f"{done} completed threads vs {active} active - archive completed to keep signal high.",
                points_lost=max_pts - pts,
            )
        )
        return pts, findings
    # also lint RECENT SESSIONS overflow
    recent = find_section(sections, "RECENT SESSIONS")
    if recent:
        recent_entries = [
            ln for ln in strip_html_comments(recent.body).splitlines() if re.match(r"^\s*-\s+", ln)
        ]
        if len(recent_entries) > MAX_RECENT_SESSIONS:
            pts = max_pts * 0.7
            findings.append(
                Finding(
                    "INFO",
                    f"RECENT SESSIONS has {len(recent_entries)} entries (target <={MAX_RECENT_SESSIONS}). "
                    "Move oldest to WORKSPACE_BRAIN_ARCHIVE.md.",
                    points_lost=max_pts - pts,
                )
            )
            return pts, findings
    return max_pts, [Finding("OK", f"{active} active / {done} completed threads - hygiene OK.")]


# ---------- main -----------------------------------------------------------


def lint(file_path: str) -> int:
    if not os.path.exists(file_path):
        print(f"brain_lint: file not found: {file_path}")
        print("Pass a path or run from a project root with WORKSPACE_BRAIN.md.")
        return 0
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    sections = parse_sections(text)
    line_count = len(text.splitlines())
    kb = len(text.encode("utf-8")) / 1024

    scorers = [
        ("Required sections", lambda: score_required_sections(sections)),
        ("Size budget", lambda: score_size(text)),
        ("Header freshness", lambda: score_freshness(text, file_path)),
        ("Section balance", lambda: score_balance(sections)),
        ("Decision rationale", lambda: score_decision_rationale(sections)),
        ("Thread hygiene", lambda: score_thread_hygiene(sections)),
    ]

    total = 0.0
    all_findings: List[Tuple[str, Finding]] = []
    breakdown: List[Tuple[str, float, float]] = []
    for axis, fn in scorers:
        pts, findings = fn()
        # max pts is inferred from first OK score where points_lost == 0
        # but easier: keep weights mirrored in the function returns
        weights = {
            "Required sections": 20,
            "Size budget": 20,
            "Header freshness": 20,
            "Section balance": 15,
            "Decision rationale": 15,
            "Thread hygiene": 10,
        }
        breakdown.append((axis, pts, weights[axis]))
        total += pts
        for f in findings:
            all_findings.append((axis, f))

    all_findings.sort(key=lambda x: SEVERITY_ORDER.get(x[1].severity, 9))

    print(f"brain_lint v1.0")
    print(f"File: {file_path} ({line_count} lines, {kb:.1f} KB, {len(sections)} sections)")
    print("")
    print(f"Score: {total:.0f}/100")
    print("")
    print("Breakdown:")
    for axis, pts, weight in breakdown:
        bar_filled = int(round(20 * pts / weight)) if weight else 0
        bar = "#" * bar_filled + "." * (20 - bar_filled)
        print(f"  [{bar}] {axis:<22} {pts:5.1f} / {weight}")
    print("")
    print("Findings (most severe first):")
    for axis, f in all_findings:
        tag = f"[{f.severity}]".ljust(8)
        loss = f" (-{f.points_lost:.0f} pts)" if f.points_lost > 0 else ""
        print(f"  {tag} {axis}: {f.msg}{loss}")
    print("")
    print("Run /brain-grade for AI-assisted review and concrete edit suggestions.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    sys.exit(lint(path))
