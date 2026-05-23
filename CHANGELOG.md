# Changelog

All notable changes to this project will be documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/).

## [Unreleased]

## [0.2.0] — 2026-05-23

The "extraordinary first impression" pass.

### Added
- **`template/brain-viewer.html`** — self-contained interactive viewer with
  dark/light themes, animated force-directed synapse graph, section cards.
  Renders any `WORKSPACE_BRAIN.md` served over `python -m http.server`.
  Generic port of the battle-tested BoneVision viewer.
- **`eval/abtest.py`** — A/B harness using the Anthropic SDK. Asks Claude 5
  brain-dependent questions with/without the brain, judge model scores
  both blind 0-30, reports mean delta + 95% CI. Prompt caching cuts brain
  cost ~90%. `--dry-run` validates without API calls. Required:
  `pip install anthropic`, `ANTHROPIC_API_KEY`.
- **`/brain-init` slash command** — 6-question Q&A flow that scaffolds a
  personalized brain in 60 sec.
- **`/brain-archive` slash command** — auto-migrates stale completed
  threads + old sessions to `WORKSPACE_BRAIN_ARCHIVE.md`, with an approval
  gate before any edits.
- **`docs/brain-viewer-hero{,-dark}.png`** — hero screenshots of viewer
  rendering a real brain, embedded in README.
- **`CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`** — project meta files.
- **`.github/ISSUE_TEMPLATE/`** — bug + feature request templates.

### Changed
- **README** — new hero with two-line tagline naming the pain, embedded
  viewer screenshot, mermaid lifecycle diagram, 3-bullet differentiator
  callout, sharpened comparison table vs Cipher / mem0 / memory-compiler /
  MemU, real-usage callout with concrete numbers from BoneVision.
- **Brain viewer accepts `?theme=dark|light` URL param** to override the
  default light theme; useful for headless screenshots and embedded demos.

### Fixed
- `brain_lint.py` no longer crashes on emoji in section titles (UTF-8
  stdout reconfigure).

## [0.1.0] — 2026-05-23

Initial public release.

### Added
- `SessionStart` hook (`brain_session_start.py`) — injects
  `WORKSPACE_BRAIN.md` at session start.
- `PreCompact` hook (`brain_pre_compact.py`) — directs Claude to flush
  state before context compaction.
- Optional `Stop` hook (`brain_stop.py`) — opportunistic flush between
  compactions, off by default.
- `/brain` and `/brain-grade` slash commands.
- `brain_lint.py` — 6-axis static quality scorer (100 pts), zero deps.
- Cross-platform installer (`install.sh`, `install.ps1`) with idempotent
  settings.json merging.
- Generic `WORKSPACE_BRAIN.md` template + research / web-app examples.
- CI smoke test workflow targeting Linux / macOS / Windows × Python 3.8 / 3.11.

[Unreleased]: https://github.com/jim4226/claude-workspace-brain/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jim4226/claude-workspace-brain/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jim4226/claude-workspace-brain/releases/tag/v0.1.0
