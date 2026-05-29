"""PreCompact hook: force a brain flush before auto-compaction loses state.

WHY THIS HOOK EMITS JSON, NOT A PRINTED DIRECTIVE
    Claude Code injects hook *stdout* into the model's context for only a few
    events (SessionStart, UserPromptSubmit, UserPromptExpansion). PreCompact is
    NOT one of them - its stdout goes only to the debug log, so a printed
    "directive" would never reach Claude. The single channel PreCompact has to
    the model is decision control: emitting

        {"decision": "block", "reason": "..."}

    pauses the compaction and feeds `reason` to Claude as an instruction.

WHAT IT DOES
    Blocks an *auto* compaction exactly once to give Claude a turn to flush
    in-flight state into WORKSPACE_BRAIN.md, then lets compaction proceed. The
    complementary SessionStart hook re-injects the (now-updated) brain after
    compaction and asks Claude to reconcile anything still missing.

SAFETY GUARDS (this hook must never wedge a session)
  * Manual `/compact` is always allowed through - the user asked for it.
  * One-shot: after blocking, a short-lived marker file lets the *next*
    compaction through, so we never loop. The marker expires after
    BRAIN_PRECOMPACT_TTL_MIN minutes (default 10), enabling a fresh flush later.
  * Fail-open: any error (bad stdin, unwritable marker, ...) allows compaction.

Env:
    BRAIN_FILE                Brain filename (default WORKSPACE_BRAIN.md)
    BRAIN_PRECOMPACT_TTL_MIN  One-shot marker TTL in minutes (default 10)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

FLUSH_REASON = (
    "Auto-compaction was paused once so you can preserve working state first. "
    "Compaction is LOSSY. Before it runs, update {brain} at the project root "
    "with anything from this session that should survive. Use the Edit tool and "
    "preserve the existing section structure:\n"
    "1. ACTIVE FOCUS - refresh the current goal/sprint if priorities shifted.\n"
    "2. ACTIVE THREADS - mark finished items done; add new in-flight items.\n"
    "3. DECISIONS LOG - prepend today's decisions WITH the reason "
    "(`- **YYYY-MM-DD**: <decision>. Reason: <why>.`).\n"
    "4. SYNAPSES - add cross-references discovered this session.\n"
    "5. KEY NUMBERS - freeze any new metrics, dimensions, or dates.\n"
    "6. RECENT SESSIONS - prepend a one-line summary of this session.\n"
    "7. OPEN QUESTIONS - surface anything still unresolved.\n"
    "Skip anything already in CLAUDE.md, git log, or derivable from code. "
    "Do this now; compaction will proceed automatically afterward."
)


def _marker_path() -> str:
    """Per-project marker in the OS temp dir (keyed by cwd) so we never write
    into - or risk committing files inside - the user's repository."""
    key = hashlib.sha1(os.getcwd().encode("utf-8")).hexdigest()[:12]
    return os.path.join(tempfile.gettempdir(), f"cwb_precompact_{key}")


def _recently_flushed(ttl_min: int) -> bool:
    """True if we blocked+flushed within the TTL window (so allow this one)."""
    try:
        age = time.time() - os.path.getmtime(_marker_path())
    except OSError:
        return False
    return age <= ttl_min * 60


def _record_flush() -> bool:
    """Stamp the marker. Returns False if it couldn't be written (fail-open)."""
    try:
        with open(_marker_path(), "w", encoding="utf-8") as f:
            f.write(str(time.time()))
        return True
    except OSError:
        return False


def decide(trigger: str, recently_flushed: bool) -> bool:
    """Pure policy: should we BLOCK this compaction to force a flush?

    Block only an auto compaction that we haven't already handled this window.
    Manual compaction and unknown triggers are always allowed (fail-open).
    """
    if trigger != "auto":
        return False
    if recently_flushed:
        return False
    return True


def main() -> int:
    try:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

        payload = {}
        try:
            if not sys.stdin.isatty():
                raw = sys.stdin.read()
                if raw.strip():
                    payload = json.loads(raw)
        except Exception:
            payload = {}

        trigger = (payload.get("trigger") or payload.get("matcher") or "").lower()
        ttl_min = int(os.environ.get("BRAIN_PRECOMPACT_TTL_MIN", "10"))

        if not decide(trigger, _recently_flushed(ttl_min)):
            return 0  # allow compaction (emit nothing)

        # Record the one-shot marker first; if we can't, fail open so a
        # persistently-unwritable marker never turns into a block loop.
        if not _record_flush():
            return 0

        brain = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")
        print(json.dumps({"decision": "block", "reason": FLUSH_REASON.format(brain=brain)}))
        return 0
    except Exception:
        # Absolute fail-open: never block compaction because of a hook error.
        return 0


if __name__ == "__main__":
    sys.exit(main())
