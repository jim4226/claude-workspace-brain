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
RESEARCH_FILENAME = os.environ.get("RESEARCH_FILE", "WORKSPACE_RESEARCH.md")
LOOPS_FILENAME = os.environ.get("LOOPS_FILE", "WORKSPACE_LOOPS.md")
MAX_KB = int(os.environ.get("BRAIN_MAX_KB", "32"))

brain_path = os.path.join(os.getcwd(), BRAIN_FILENAME)
research_path = os.path.join(os.getcwd(), RESEARCH_FILENAME)
loops_path = os.path.join(os.getcwd(), LOOPS_FILENAME)

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

# Discoverability breadcrumb: tell future-Claude the research sidecar exists.
# The sidecar is NOT injected (it can be large); the brain's SYNAPSES section
# tells you when to consult it. This one-liner ensures it's never invisible.
if os.path.exists(research_path):
    try:
        research_kb = os.path.getsize(research_path) / 1024
        print("")
        print(
            f"(Adjacent: {RESEARCH_FILENAME} exists ({research_kb:.1f} KB) — "
            f"user-research log with pseudonymous insights. Read on demand "
            f"or via /user-research consult.)"
        )
    except Exception:
        pass

# Loops breadcrumb: surface the count of self-improving loops and how many
# are due today. We deliberately don't inject loop bodies — the runner hook
# (brain_loop_runner.py) handles due-loop directives if enabled.
if os.path.exists(loops_path):
    try:
        import re
        from datetime import datetime, timezone
        loops_text = open(loops_path, encoding="utf-8").read()
        # Each loop is a `## LOOP: <slug>` section.
        slugs = re.findall(r"^##\s+LOOP:\s+(\S+)\s*$", loops_text, re.MULTILINE)
        # A loop is "due" if its Next run date is on or before today
        # AND its Status is not paused/retired.
        today = datetime.now(timezone.utc).date()
        due_count = 0
        # Walk loop sections one at a time to read Next run + Status pairs.
        sections = re.split(r"^##\s+LOOP:\s+\S+\s*$", loops_text, flags=re.MULTILINE)[1:]
        for section in sections:
            status_m = re.search(r"^-\s+\*\*Status\*\*:\s+(\S+)", section, re.MULTILINE)
            status = (status_m.group(1).lower().strip(".") if status_m else "active")
            if status in ("paused", "retired"):
                continue
            nr_m = re.search(r"^-\s+\*\*Next run\*\*:\s+(\S+)", section, re.MULTILINE)
            nr_val = (nr_m.group(1).strip().rstrip(".") if nr_m else "")
            if nr_val.lower() in ("manual", "—", "tbd", ""):
                continue
            try:
                nr_date = datetime.strptime(nr_val, "%Y-%m-%d").date()
            except ValueError:
                continue
            if nr_date <= today:
                due_count += 1
        print("")
        if due_count:
            print(
                f"(Adjacent: {LOOPS_FILENAME} — {len(slugs)} self-improving "
                f"loop(s), {due_count} due. Run /loop for status or "
                f"/loop-run <slug> to act.)"
            )
        else:
            print(
                f"(Adjacent: {LOOPS_FILENAME} — {len(slugs)} self-improving "
                f"loop(s), none due. /loop for status.)"
            )
    except Exception:
        pass

print("")
print("## ===== END BRAIN — resume work =====")
