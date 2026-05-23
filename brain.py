"""brain - unified CLI for the workspace brain.

For claude.ai users (or any AI chat without hooks): use this CLI to copy your
brain to clipboard, lint it, view it in a browser, or run the eval harness
against any model that speaks the Anthropic API.

For Claude Code users: the SessionStart + PreCompact hooks already automate
brain injection. This CLI is still useful for `lint` and `serve` outside an
active Claude Code session.

Usage:
    python brain.py copy            # copy WORKSPACE_BRAIN.md to clipboard
    python brain.py show            # print brain to stdout
    python brain.py lint            # 6-axis quality scorer
    python brain.py serve [--port N]   # launch HTML viewer in browser
    python brain.py eval [--runs N]    # A/B harness vs your brain
    python brain.py --help

Brain file resolution: defaults to ./WORKSPACE_BRAIN.md, override with
--brain PATH on any subcommand.
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent


def find_brain(explicit: Path | None) -> Path:
    if explicit:
        if not explicit.exists():
            print(f"ERROR: brain not found at {explicit}", file=sys.stderr)
            sys.exit(2)
        return explicit
    candidate = Path.cwd() / "WORKSPACE_BRAIN.md"
    if not candidate.exists():
        print(
            "ERROR: no WORKSPACE_BRAIN.md in current directory. "
            "Pass --brain PATH or `cd` to a project root that has one.",
            file=sys.stderr,
        )
        sys.exit(2)
    return candidate


def cmd_show(args: argparse.Namespace) -> int:
    brain = find_brain(args.brain)
    sys.stdout.write(brain.read_text(encoding="utf-8"))
    if not brain.read_text(encoding="utf-8").endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_copy(args: argparse.Namespace) -> int:
    brain = find_brain(args.brain)
    content = brain.read_text(encoding="utf-8")
    system = platform.system()
    try:
        if system == "Windows":
            proc = subprocess.run(["clip"], input=content, text=True, encoding="utf-8", check=True)
        elif system == "Darwin":
            proc = subprocess.run(["pbcopy"], input=content, text=True, encoding="utf-8", check=True)
        else:  # Linux/BSD
            for tool in (["xclip", "-selection", "clipboard"], ["wl-copy"], ["xsel", "-b", "-i"]):
                try:
                    subprocess.run(tool, input=content, text=True, encoding="utf-8", check=True)
                    break
                except FileNotFoundError:
                    continue
            else:
                print(
                    "ERROR: no clipboard tool found. Install xclip / xsel / wl-copy, "
                    "or use `python brain.py show | <your-clipboard-tool>`.",
                    file=sys.stderr,
                )
                return 3
        kb = len(content.encode("utf-8")) / 1024
        print(f"Copied {brain.name} to clipboard ({kb:.1f} KB, {len(content.splitlines())} lines).")
        print("Paste it into your AI chat (claude.ai, ChatGPT, etc.) at the start of a long session,")
        print("or upload as Project knowledge in claude.ai Projects for persistent context.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: clipboard tool failed: {e}", file=sys.stderr)
        return 3


def cmd_lint(args: argparse.Namespace) -> int:
    brain = find_brain(args.brain)
    linter = REPO_ROOT / "template" / ".claude" / "scripts" / "brain_lint.py"
    if not linter.exists():
        # Fallback to in-project linter if running from outside the repo
        candidate = Path.cwd() / ".claude" / "scripts" / "brain_lint.py"
        if candidate.exists():
            linter = candidate
        else:
            print(f"ERROR: brain_lint.py not found (looked in {linter} and {candidate})", file=sys.stderr)
            return 4
    return subprocess.call([sys.executable, str(linter), str(brain)])


def cmd_serve(args: argparse.Namespace) -> int:
    brain = find_brain(args.brain)
    viewer = REPO_ROOT / "template" / "brain-viewer.html"
    if not viewer.exists():
        candidate = Path.cwd() / "template" / "brain-viewer.html"
        if not candidate.exists():
            candidate = Path.cwd() / "brain-viewer.html"
        if candidate.exists():
            viewer = candidate
        else:
            print(f"ERROR: brain-viewer.html not found.", file=sys.stderr)
            return 4

    # Serve the brain's parent directory so the viewer can fetch it
    serve_root = brain.parent
    rel_viewer = os.path.relpath(viewer, serve_root).replace(os.sep, "/")
    rel_brain = brain.name
    port = args.port

    print(f"Serving {serve_root} on http://localhost:{port}")
    print(f"Opening viewer: http://localhost:{port}/{rel_viewer}?path={rel_brain}&theme={args.theme}")
    print("Ctrl-C to stop.")

    url = f"http://localhost:{port}/{rel_viewer}?path={rel_brain}&theme={args.theme}"
    # Open browser shortly after server starts
    import threading
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    # Run http.server inline (blocks until Ctrl-C)
    cmd = [sys.executable, "-m", "http.server", str(port), "--directory", str(serve_root)]
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 0


def cmd_eval(args: argparse.Namespace) -> int:
    eval_script = REPO_ROOT / "eval" / "abtest.py"
    if not eval_script.exists():
        print(f"ERROR: eval harness not found at {eval_script}", file=sys.stderr)
        return 4
    cli = [sys.executable, "-m", "eval.abtest"]
    if args.runs:
        cli += ["--runs", str(args.runs)]
    if args.brain:
        cli += ["--brain", str(args.brain)]
    if args.dry_run:
        cli += ["--dry-run"]
    return subprocess.call(cli, cwd=str(REPO_ROOT))


def main() -> int:
    p = argparse.ArgumentParser(
        prog="brain",
        description="Unified CLI for the workspace brain. Use with Claude Code, claude.ai, or any AI chat.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_brain_arg(parser):
        parser.add_argument("--brain", type=Path, default=None,
                            help="Path to WORKSPACE_BRAIN.md (default: ./WORKSPACE_BRAIN.md)")

    p_show = sub.add_parser("show", help="Print brain content to stdout")
    add_brain_arg(p_show)
    p_show.set_defaults(func=cmd_show)

    p_copy = sub.add_parser("copy", help="Copy brain to clipboard (paste into any AI chat)")
    add_brain_arg(p_copy)
    p_copy.set_defaults(func=cmd_copy)

    p_lint = sub.add_parser("lint", help="Run 6-axis quality scorer")
    add_brain_arg(p_lint)
    p_lint.set_defaults(func=cmd_lint)

    p_serve = sub.add_parser("serve", help="Launch HTML viewer in browser")
    add_brain_arg(p_serve)
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--theme", choices=["dark", "light"], default="light")
    p_serve.set_defaults(func=cmd_serve)

    p_eval = sub.add_parser("eval", help="A/B harness: does the brain help on your project?")
    add_brain_arg(p_eval)
    p_eval.add_argument("--runs", type=int, default=None)
    p_eval.add_argument("--dry-run", action="store_true")
    p_eval.set_defaults(func=cmd_eval)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
