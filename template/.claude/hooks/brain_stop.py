"""Stop hook (opt-in): block one stop to flush the brain if it's gone stale.

PreCompact only fires when context is about to overflow. For long-running
sessions that never hit the compaction boundary - or for users who close
sessions cleanly before compaction - decisions can still be lost.

Like PreCompact, a Stop hook CANNOT inject context via stdout (that goes only
to the debug log). The single channel to the model is decision control:
emitting {"decision": "block", "reason": "..."} prevents the stop and feeds
`reason` to Claude as an instruction, so it can flush the brain before ending.

This hook blocks the stop only when the brain hasn't been touched in
BRAIN_STOP_INTERVAL_MIN minutes (default: 30), so it doesn't nag every turn.

SAFETY GUARDS (never loop):
  * stop_hook_active: if we're already inside a stop-hook continuation, allow
    the stop immediately.
  * Fail-open: any error allows the stop.

Opt in by adding the Stop block to `.claude/settings.json` (the installer's
--with-stop-hook flag does this for you).
"""
import json
import os
import sys
import time


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

        # Already continuing because of a previous Stop block -> let it stop.
        if payload.get("stop_hook_active"):
            return 0

        brain_file = os.environ.get("BRAIN_FILE", "WORKSPACE_BRAIN.md")
        interval_min = int(os.environ.get("BRAIN_STOP_INTERVAL_MIN", "30"))

        brain_path = os.path.join(os.getcwd(), brain_file)
        if not os.path.exists(brain_path):
            return 0

        age_sec = time.time() - os.path.getmtime(brain_path)
        if age_sec < interval_min * 60:
            return 0

        age_min = int(age_sec // 60)
        reason = (
            f"{brain_file} hasn't been updated in {age_min} min. Before ending: if "
            "this session produced anything worth preserving - a decision (with its "
            "reason), a new in-flight thread, a key number, a resolved question - "
            "update the brain now with the Edit tool. If nothing is worth saving, "
            "say so in one line and stop."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except Exception:
        # Fail-open: never trap the user in a session because of a hook error.
        return 0


if __name__ == "__main__":
    sys.exit(main())
