"""SessionStart hook: inject WORKSPACE_BRAIN.md into Claude's context.

Stdout from a SessionStart hook IS added to Claude's context (SessionStart,
UserPromptSubmit, and UserPromptExpansion are the only events for which plain
stdout reaches the model). This hook uses that to restore curated state that
summarisation would otherwise collapse.

It fires for every session source. The framing adapts to the source:
  * compact            -> a compaction just ran (lossy). Re-inject the brain as
                          ground truth AND ask Claude to reconcile any in-flight
                          state the summary dropped but that the brain lacks.
  * startup/resume/...  -> normal "here is your persistent memory" framing.

Configuration (read from environment, with sensible defaults):
    BRAIN_FILE   Path to the brain file, relative to project root.
                 Default: WORKSPACE_BRAIN.md
    BRAIN_MAX_KB Soft cap on injected size. If the file is larger, only
                 the first BRAIN_MAX_KB kilobytes are injected and a
                 truncation notice is appended. Default: 32.

Cross-platform notes:
  * Windows consoles default to cp1252; we reconfigure stdout to UTF-8
    so emojis in section headers survive.
  * On macOS/Linux the reconfigure call is a no-op.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BRAIN_FILENAME = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")
MAX_KB = int(os.environ.get("BRAIN_MAX_KB", "32"))

# What kicked off this session: startup / resume / clear / compact.
source = ""
try:
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
            source = (payload.get("source") or payload.get("matcher") or "").lower()
except Exception:
    source = ""

brain_path = os.path.join(os.getcwd(), BRAIN_FILENAME)

if source == "compact":
    print("## ===== WORKSPACE BRAIN (re-loaded after compaction) =====")
    print("A context compaction just ran - working memory was summarised and is lossy.")
    print("The brain below is the durable, curated ground truth. Reconcile against it:")
    print("if anything you were mid-task on is NOT captured below, record it now with")
    print("the Edit tool before continuing.")
else:
    print("## ===== WORKSPACE BRAIN (auto-loaded at SessionStart) =====")
    print("This is the curated, compaction-proof memory of the workspace.")
    print("Treat it as ground truth for current state, active threads, and decisions.")
    print("Update it via the Edit tool whenever something worth preserving happens.")
print("")

if os.path.exists(brain_path):
    try:
        with open(brain_path, "r", encoding="utf-8") as f:
            contents = f.read()
        max_bytes = MAX_KB * 1024
        if len(contents.encode("utf-8")) > max_bytes:
            truncated = contents.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
            sys.stdout.write(truncated)
            print("")
            print(f"... (brain truncated at {MAX_KB} KB — consider archiving older sections)")
        else:
            sys.stdout.write(contents)
            if not contents.endswith("\n"):
                print("")
    except Exception as e:
        print(f"(Failed to read {BRAIN_FILENAME}: {e})")
else:
    print(f"(Brain file {BRAIN_FILENAME} not found at project root.")
    print(" Create it from the template to enable persistent memory:")
    print(" https://github.com/jim4226/claude-workspace-brain#quick-start)")

print("")
print("## ===== END BRAIN — resume work =====")
