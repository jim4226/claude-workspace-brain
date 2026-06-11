# Changelog

All notable changes to this project will be documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[SemVer](https://semver.org/).

## [Unreleased]

### Added
- **Self-improving loops** backed by the brain. A loop *defines itself*
  via `/loop-init` (interactive factory that requires a falsifiable
  criterion), *runs itself* via `/loop-run` (append-only History with
  refusal-to-fabricate guarantees), and *improves itself* via
  `/loop-tune` (one-field refinement per run, requires ≥3 prior runs
  for evidence, mirrors approved tunings into `DECISIONS LOG` with
  `Reason:` so the brain's lint rationale axis catches lazy tuning).
  `/loop` gives read-only status (due now / due soon / stable /
  failing / paused-retired).
- **`WORKSPACE_LOOPS.md`** sidecar (mirrors `WORKSPACE_RESEARCH.md`)
  holding loop specs, append-only History, and append-only Tuning Log.
  NOT auto-injected. Each loop's `Trigger` and `Next run` are honored
  by an opt-in Stop hook.
- **`brain_loop_runner.py`** opt-in Stop hook that surfaces *due*
  loops with a terse directive (one line per due loop). De-duplicates
  within a 6h quiet window (`LOOPS_QUIET_HOURS` env var) so it won't
  spam every Stop event. Refuses to run observation commands itself —
  only the slash command does, with user awareness.
- **`brain_loop_autopilot.py`** opt-in Stop hook that *drives* due
  loops by emitting a `{"decision": "block", "reason": …}` JSON
  response — Claude Code's Stop-hook protocol blocks the stop and
  hands Claude the directive to `/loop-run <slug>`. Bounded by four
  guards: (1) `BRAIN_LOOPS_OFF=1` kill switch, (2) session-wide block
  cap (`BRAIN_LOOP_MAX_PER_SESSION`, default 2), (3) per-loop session
  cap (`BRAIN_LOOP_MAX_PER_LOOP`, default 1), (4) anti-spin (if last
  block produced no new History entry, allow the stop — cannot be
  disabled). State lives in tempdir keyed by SHA-1(cwd), 7-day TTL,
  never written into the repo. Any exception allows the stop.
- **`_install.py --with-loop-autopilot`** flag wires the autopilot
  Stop hook (separate from `--with-loop-runner` — pick one trigger
  mode based on how autonomous you want loops to be).
- **`/loop-suggest` slash command** — reads
  `WORKSPACE_BRAIN.md` (+ `WORKSPACE_RESEARCH.md` if present),
  extracts loop-worthy signal across 7 brain sections and 2 research
  patterns, scores candidates 1-9 on signal / falsifiability / brain
  coupling, drops anything below 6, ranks descending, and proposes
  the top 1-3 with pre-filled `Goal` / `Observation` / `Criterion` /
  `Trigger` (conservative default `manual`) / `Brain context` /
  `First-failure action`. Each proposal includes a "Why this loop?"
  block citing at least two brain quotes. Read-mostly: writes nothing
  unless the user approves a `/loop-init` invocation. Closes the
  "loops build by themselves" gap — the brain already contains the
  signal, you just confirm.
- **`template/.claude/scripts/loops_lint.py`** — static quality
  scorer for `WORKSPACE_LOOPS.md` mirroring `brain_lint.py`. Six axes,
  100 points: Required fields (25), History hygiene (15), Tuning
  rationale (20), Trigger sanity (15), Stale Next-run (15), Status
  consistency (10). Stdlib only, always exits 0, no third-party deps.
- **`brain_session_start.py`** now emits a one-line loops breadcrumb
  noting total loop count and due count. Honors `LOOPS_FILE` env var.
- **`_install.py --with-loop-runner`** flag wires the loop runner Stop
  hook (mirrors `--with-stop-hook` shape).
- **Installer now ships all command files** — previously `/brain-init`
  and `/brain-archive` weren't being copied; they are now, alongside
  the new `/user-research` and `/loop-*` commands.
- **CI workflow** verifies the loop runner exits cleanly with no loops
  file present and emits a directive when a due loop is defined.
- **`/user-research` slash command** — captures atomic user-research
  insights into a sidecar `WORKSPACE_RESEARCH.md` (kept out of the
  brain's size budget). Provenance-checked: pseudonyms only, never real
  names; refuses to fabricate participants, dates, or quotes. Two
  confidence buckets (`[anecdote]` N=1, `[pattern]` N≥2 in same segment)
  — qual N never reaches "strong." `[pattern]` insights gate-edit the
  brain: thread annotations, OPEN QUESTIONS additions (capped per run),
  one-time SYNAPSES pointers. `[anecdote]` insights stay in the sidecar
  unless explicitly escalated. Conflicts with prior decisions route to
  OPEN QUESTIONS (DECISIONS LOG stays append-only). Four input modes:
  `describe`, `from-notes`, `synthesize`, and read-only `consult`.
  Re-identification check (role+org+region+time tuple) gates writes;
  verbatim quotes are routed to a gitignored `./research/quotes.local.md`.
  Reports a behavior-vs-opinion ratio (Mom-Test discipline) and lint
  delta on every run.
- **`examples/user-research-walkthrough.md`** — fully worked 5-interview
  checkout study showing input → sidecar entry → gated brain edits →
  report.
- **`brain_session_start.py`** now emits a one-line discoverability
  breadcrumb when `WORKSPACE_RESEARCH.md` exists (so future-Claude knows
  to consult it via `/user-research consult`). Honors `RESEARCH_FILE`
  env var.

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

[Unreleased]: https://github.com/jim4226/claude-workspace-brain/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jim4226/claude-workspace-brain/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jim4226/claude-workspace-brain/releases/tag/v0.1.0
