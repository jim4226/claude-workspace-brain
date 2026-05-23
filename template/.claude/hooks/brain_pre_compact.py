"""PreCompact hook: nudge Claude to flush state into the brain before
context compaction.

Fires immediately before Claude Code compresses the conversation. Stdout
is injected as a system directive so Claude sees it in time to update
WORKSPACE_BRAIN.md before the summary collapses the working state.

Why this matters: compaction is lossy. Decisions, in-flight threads,
key numbers, and recent-session context all get squeezed. The brain
file survives because it lives on disk; this hook is the trigger that
moves what's in working context into that durable form.
"""
import os
import sys
import json
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

trigger = "unknown"
try:
    payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    trigger = payload.get("trigger") or payload.get("matcher") or "unknown"
except Exception:
    payload = {}

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
brain = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")

print("## CRITICAL - PRE-COMPACTION DIRECTIVE")
print("")
print(f"Context compaction is about to run (trigger: {trigger}, time: {ts}).")
print(f"Compaction is LOSSY. Before it runs, you MUST update {brain} at the")
print("project root with everything from this session that should persist.")
print("")
print("Use the **Edit** tool. Preserve existing section structure. Specifically:")
print("")
print("1. **ACTIVE FOCUS** - refresh the current goal / current sprint if priorities shifted.")
print("2. **ACTIVE THREADS** - mark completed items with a check (move to bottom),")
print("   add new in-flight items uncovered this session.")
print("3. **DECISIONS LOG** - prepend today's decisions with rationale (the WHY,")
print("   not just the WHAT). Format: `- **YYYY-MM-DD**: <decision>. Reason: <why>.`")
print("4. **SYNAPSES** - add new cross-references (A <-> B) discovered this session.")
print("5. **KEY NUMBERS** - add any new metrics, dimensions, dates worth freezing.")
print("6. **RECENT SESSIONS** - prepend a one-line summary of this session.")
print("   If the list exceeds ~10 entries, move the oldest to WORKSPACE_BRAIN_ARCHIVE.md.")
print("7. **OPEN QUESTIONS** - surface anything still unresolved.")
print("")
print("Skip anything already in MEMORY.md, CLAUDE.md, git log, or derivable from code.")
print("This brain is for state that would otherwise be lost.")
print("")
print("Do this NOW, in your very next response, before any other work.")
print("Then proceed with whatever the user asks. The SessionStart hook will")
print("re-inject the updated brain on the next session - that is how quality")
print("survives the compact boundary.")
print("")
print("## END DIRECTIVE")
