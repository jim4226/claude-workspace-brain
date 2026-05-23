# Contributing to claude-workspace-brain

Thanks for the interest. The repo is intentionally small, so changes
should preserve that: minimal dependencies, deterministic behavior,
zero magic.

## Filing issues

| Type | Where |
|------|-------|
| Bug | [Bug report template](.github/ISSUE_TEMPLATE/bug_report.md) |
| Feature request | [Feature request template](.github/ISSUE_TEMPLATE/feature_request.md) |
| Question / discussion | [GitHub Discussions](https://github.com/jim4226/claude-workspace-brain/discussions) |

For bugs, include: OS, Python version, exact command, full output. The CI
matrix tests Linux / macOS / Windows × Python 3.8 / 3.11 — bugs that
reproduce there are easiest to fix.

## Pull requests

Small focused PRs land fastest. Before opening one:

1. **Run the linter on your changes** if they touch the brain template:
   ```bash
   python template/.claude/scripts/brain_lint.py template/WORKSPACE_BRAIN.md
   ```
2. **Run the installer into a throwaway directory** if you touched the
   installer or hooks:
   ```bash
   python _install.py --target /tmp/cwb-test --yes
   ```
3. **Smoke-test the eval in dry-run** if you touched it:
   ```bash
   python -m eval.abtest --dry-run
   ```
4. Add or update `CHANGELOG.md` under `## [Unreleased]`.

## What we're looking for

| Priority | Area | Examples |
|----------|------|----------|
| High | Hook ports | Node, Bash, Go versions of the two hooks |
| High | Project-type templates | Add to `examples/` — game-dev, infra, mobile, etc. |
| Medium | Linter rule refinements | New axes that catch real brain rot patterns |
| Medium | Eval harness | More held-out questions, alternate judge prompts, better aggregation |
| Low | Viewer features | Filter by section, search, edit-in-place |

## What we're not looking for

- **Auto-extraction features** (compiling brains from transcripts). That's
  what [claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler)
  does and they do it well. This repo's value is the *hand-curated* path.
- **External-service integrations** (mem0, MemU). Same reason — those
  exist; we're the zero-deps alternative.
- **PyPI packaging** until v1.0. Not against it, just want the install
  story to stay "one curl line" until the API is settled.

## Code style

- Python: stdlib-only for hooks + linter; `anthropic` SDK for the eval
  harness only. No type-checking enforced, but type hints encouraged on
  public functions.
- JavaScript (in `brain-viewer.html`): vanilla, no build step, no
  dependencies. Self-contained single file.
- Markdown: ATX-style headers (`## Heading`), no trailing whitespace,
  one sentence per line in source if possible (easier to diff).

## Releasing (maintainers)

1. Bump version in `CHANGELOG.md` (move `## [Unreleased]` to a new
   `## [X.Y.Z] — YYYY-MM-DD` block).
2. Commit: `chore: release vX.Y.Z`.
3. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
4. Push: `git push && git push --tags`.
5. Create GitHub release from the tag with the changelog block as body.
