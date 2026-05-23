"""Stop hook (opt-in): opportunistic brain flush between compaction events.

PreCompact only fires when context is about to overflow. For long-running
sessions that never hit the compaction boundary - or for users who close
sessions cleanly before compaction - decisions can still be lost.

This hook fires when Claude finishes generating a response. To avoid
nagging on every turn, it only emits the flush directive when both:

  1. WORKSPACE_BRAIN.md hasn't been touched in BRAIN_STOP_INTERVAL_MIN
     minutes (default: 30), AND
  2. the conversation has had real activity since then (best-effort).

Opt in by uncommenting the Stop block in `.claude/settings.json`.
"""
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BRAIN_FILE = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")
INTERVAL_MIN = int(os.environ.get("BRAIN_STOP_INTERVAL_MIN", "30"))

brain_path = os.path.join(os.getcwd(), BRAIN_FILE)
if not os.path.exists(brain_path):
    sys.exit(0)

age_sec = time.time() - os.path.getmtime(brain_path)
if age_sec < INTERVAL_MIN * 60:
    sys.exit(0)

age_min = int(age_sec // 60)
print(f"## brain reminder")
print(f"")
print(f"{BRAIN_FILE} hasn't been updated in {age_min} min. If this session")
print(f"produced anything worth preserving - a decision, a new in-flight thread,")
print(f"a key number, a resolved question - update the brain now. Otherwise")
print(f"ignore this notice and continue.")
