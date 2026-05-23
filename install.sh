#!/usr/bin/env bash
# claude-workspace-brain installer (POSIX wrapper around _install.py)
#
# Usage from a cloned repo:
#   ./install.sh [--target <path>] [--force] [--yes] [--with-stop-hook]
#
# Usage as a one-liner (clones into ~/.cache and installs to cwd):
#   curl -sSL https://raw.githubusercontent.com/jim4226/claude-workspace-brain/main/install.sh | bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# If invoked via curl|bash, BASH_SOURCE points to /dev/stdin and there is no
# local template/ directory. Clone the repo to a cache dir first.
if [ ! -d "$SCRIPT_DIR/template" ]; then
  CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/claude-workspace-brain"
  echo "Bootstrap: cloning repo into $CACHE_DIR ..."
  rm -rf "$CACHE_DIR"
  git clone --depth=1 https://github.com/jim4226/claude-workspace-brain.git "$CACHE_DIR"
  SCRIPT_DIR="$CACHE_DIR"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  else
    echo "ERROR: Python 3.8+ required (set PYTHON_BIN env var to override)."
    exit 1
  fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/_install.py" "$@"
