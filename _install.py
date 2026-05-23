"""Installer for claude-workspace-brain.

Copies template/.claude/* and template/WORKSPACE_BRAIN.md into a target
project directory. Merges with any existing settings.json. Refuses to
overwrite existing files without --force.

Usage:
    python _install.py [--target <path>] [--force] [--yes] [--with-stop-hook]

Defaults:
    --target  current working directory
    --force   off (skip files that already exist)
    --yes     off (prompts before writing)
    --with-stop-hook  off (enables the opportunistic Stop hook)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = REPO_ROOT / "template"

# Files to copy: (source relative to template/, destination relative to target/)
FILES = [
    (".claude/hooks/brain_session_start.py", ".claude/hooks/brain_session_start.py"),
    (".claude/hooks/brain_pre_compact.py", ".claude/hooks/brain_pre_compact.py"),
    (".claude/hooks/brain_stop.py", ".claude/hooks/brain_stop.py"),
    (".claude/commands/brain.md", ".claude/commands/brain.md"),
    (".claude/commands/brain-grade.md", ".claude/commands/brain-grade.md"),
    (".claude/scripts/brain_lint.py", ".claude/scripts/brain_lint.py"),
    ("WORKSPACE_BRAIN.md", "WORKSPACE_BRAIN.md"),
]

STOP_HOOK_BLOCK = {
    "matcher": "",
    "hooks": [
        {
            "type": "command",
            "command": "python .claude/hooks/brain_stop.py",
            "timeout": 10,
        }
    ],
}


def confirm(prompt: str, default_yes: bool) -> bool:
    if default_yes:
        return True
    ans = input(f"{prompt} [y/N] ").strip().lower()
    return ans in ("y", "yes")


def copy_with_check(src: Path, dst: Path, force: bool, yes: bool) -> str:
    """Returns 'created', 'overwritten', or 'skipped'."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if not force:
            return "skipped"
        if not yes and not confirm(f"  Overwrite {dst}?", False):
            return "skipped"
        shutil.copy2(src, dst)
        return "overwritten"
    shutil.copy2(src, dst)
    return "created"


def merge_settings(target: Path, force: bool, yes: bool, with_stop: bool) -> str:
    """Merge our hook entries into the target's settings.json (or create fresh)."""
    template_settings = json.loads((TEMPLATE_DIR / ".claude/settings.json").read_text(encoding="utf-8"))
    if with_stop:
        template_settings.setdefault("hooks", {}).setdefault("Stop", []).append(STOP_HOOK_BLOCK)

    target_settings_path = target / ".claude/settings.json"
    if not target_settings_path.exists():
        target_settings_path.parent.mkdir(parents=True, exist_ok=True)
        target_settings_path.write_text(
            json.dumps(template_settings, indent=2) + "\n", encoding="utf-8"
        )
        return "created"

    existing = json.loads(target_settings_path.read_text(encoding="utf-8"))
    existing.setdefault("hooks", {})
    merged_any = False
    for event, blocks in template_settings.get("hooks", {}).items():
        existing_blocks = existing["hooks"].setdefault(event, [])
        for new_block in blocks:
            # naive de-dupe: same command string already present?
            new_cmds = {h.get("command") for h in new_block.get("hooks", [])}
            existing_cmds = {
                h.get("command")
                for block in existing_blocks
                for h in block.get("hooks", [])
            }
            if not new_cmds.issubset(existing_cmds):
                existing_blocks.append(new_block)
                merged_any = True

    if not merged_any:
        return "already-present"
    if not force and not yes:
        if not confirm(f"  Add brain hooks to existing {target_settings_path}?", False):
            return "skipped"

    target_settings_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return "merged"


def main() -> int:
    p = argparse.ArgumentParser(description="Install claude-workspace-brain into a project.")
    p.add_argument("--target", default=os.getcwd(), help="Target project directory (default: cwd)")
    p.add_argument("--force", action="store_true", help="Overwrite existing files without prompting")
    p.add_argument("--yes", action="store_true", help="Assume yes to all prompts")
    p.add_argument("--with-stop-hook", action="store_true", help="Also enable the opt-in Stop hook")
    args = p.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: target is not a directory: {target}")
        return 1

    print(f"claude-workspace-brain installer")
    print(f"  target:         {target}")
    print(f"  source:         {TEMPLATE_DIR}")
    print(f"  force:          {args.force}")
    print(f"  with-stop-hook: {args.with_stop_hook}")
    print("")

    if not args.yes and not args.force:
        if not confirm("Proceed?", False):
            print("Aborted.")
            return 0

    results: dict[str, list[str]] = {"created": [], "overwritten": [], "skipped": [], "merged": [], "already-present": []}

    # Settings handled specially (merge instead of copy)
    status = merge_settings(target, args.force, args.yes, args.with_stop_hook)
    results.setdefault(status, []).append(".claude/settings.json")

    for src_rel, dst_rel in FILES:
        src = TEMPLATE_DIR / src_rel
        dst = target / dst_rel
        if not src.exists():
            print(f"  ! source missing: {src}")
            continue
        status = copy_with_check(src, dst, args.force, args.yes)
        results.setdefault(status, []).append(dst_rel)

    print("")
    print("Results:")
    for status, paths in results.items():
        if not paths:
            continue
        print(f"  {status}:")
        for path in paths:
            print(f"    - {path}")

    print("")
    print("Done. Next steps:")
    print(f"  1. Open {target / 'WORKSPACE_BRAIN.md'} and fill in the ACTIVE FOCUS section.")
    print(f"  2. Start a new Claude Code session in this project - hooks fire automatically.")
    print(f"  3. Try /brain or /brain-grade.")
    print(f"  4. Run `python .claude/scripts/brain_lint.py` any time to check quality.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
