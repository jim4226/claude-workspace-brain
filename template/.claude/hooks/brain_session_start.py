"""SessionStart hook: inject WORKSPACE_BRAIN.md into Claude's context.

Stdout is injected at the start of every new, resumed, or post-compaction
session. This restores curated state that summarisation would otherwise
collapse.

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
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BRAIN_FILENAME = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")
MAX_KB = int(os.environ.get("BRAIN_MAX_KB", "32"))

brain_path = os.path.join(os.getcwd(), BRAIN_FILENAME)

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
