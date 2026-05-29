# Changelog

All notable changes to this project will be documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/).

## [Unreleased]

### Fixed
- **Hooks now actually reach the model.** Claude Code only injects hook *stdout*
  into context for `SessionStart` / `UserPromptSubmit`; `PreCompact` and `Stop`
  stdout go to the debug log only. The old hooks printed flush directives Claude
  never saw. They now use the supported decision channel
  (`{"decision": "block", "reason": ...}`):
  - **`PreCompact`** blocks an *auto* compaction once and instructs Claude to
    flush state into the brain, then lets compaction proceed. Guarded: manual
    `/compact` is never blocked, a short-TTL marker (kept in the OS temp dir,
    never the repo) makes the block one-shot, and any error fails open. Tunable
    via `BRAIN_PRECOMPACT_TTL_MIN` (default 10 min).
  - **`Stop`** (opt-in) blocks one stop to flush a stale brain, guarded by
    `stop_hook_active` so it can't loop.
- **`SessionStart` reconciles after compaction.** On the `compact` source it now
  re-injects the brain *and* asks Claude to record any in-flight state the
  summary dropped.
- **Installer ships `/brain-init` and `/brain-archive`.** They were documented
  but never copied (`_install.py` installed only `brain.md` + `brain-grade.md`).
  The template is now 10 files (was 8); CI verifies all 10 and the new hook
  behavior.
- **`eval/README.md`** now points at the shipped `eval/abtest.py` A/B harness
  instead of describing it as a "TODO".
- **CHANGELOG compare links** corrected through v0.2.1.

## [0.2.1] — 2026-05-23

### Added
- **`brain.py` unified CLI** — subcommands `show`, `copy`, `lint`, `serve`, `eval`.
  Enables non-Claude-Code workflows: copy your brain to clipboard (Windows
  `clip` / macOS `pbcopy` / Linux `xclip`/`wl-copy`/`xsel`) and paste into
  any AI chat.
- **README section: "Use with claude.ai (no Claude Code required)"** explaining
  two patterns: (A) upload `WORKSPACE_BRAIN.md` as claude.ai Project knowledge
  for persistent context across chats, (B) `brain copy` + manual paste for
  ad-hoc sessions. Also lists what's lost without hooks (no automatic flush)
  vs what's kept (file structure, linter, viewer, eval).

### Changed
- **README hero subtitle** now notes the claude.ai workflow alongside Claude Code.

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

[Unreleased]: https://github.com/jim4226/claude-workspace-brain/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/jim4226/claude-workspace-brain/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/jim4226/claude-workspace-brain/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jim4226/claude-workspace-brain/releases/tag/v0.1.0
