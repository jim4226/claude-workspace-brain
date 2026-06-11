# WORKSPACE LOOPS
> Self-improving loops backed by the workspace brain. Each loop has a
> goal, an observation, a success criterion, run history, and a tuning
> log. NOT auto-injected — the SessionStart hook surfaces *due* loops
> as a one-line breadcrumb.
> Last sync: YYYY-MM-DD · Maintainer: Claude (with you)

## How to read this file

Each `## LOOP: <slug>` section defines one self-improving loop:

- **Goal** — one sentence, falsifiable. ("Keep brain lint >= 85", not
  "keep brain healthy".)
- **Trigger** — `every <N>d`, `manual`, or `on-session-start`. Controls
  when the loop runner fires the loop.
- **Observation** — a shell command (or `manual:<question>`) whose stdout
  is the observable. The runner does NOT invent results.
- **Criterion** — a Python-style boolean on the observation parse.
  ("score >= 85", "exit_code == 0", "count == 0".)
- **Brain context** — brain sections the loop runner / tuner should read
  before acting. Lets the loop reason from the brain, not from thin air.
- **Status** — `active` (running on trigger), `stable` (succeeded ≥ 5
  consecutive runs; back off frequency), `paused` (skipped), `retired`
  (kept for history).

Then two **append-only** logs:

- `### History` — one line per run: date · STATUS · observation snippet ·
  → action.
- `### Tuning Log` — one line per refinement: date · what changed ·
  Reason: why.

**Append-only rules** (mirror DECISIONS LOG):
- Never edit a past History or Tuning entry. To revisit, add a new entry.
- Tuning entries MUST include `Reason:` — the linter checks this.
- When a loop is retired, mark `Status: retired` and stop adding runs.
  Don't delete — the record is the value.

---

## LOOP: <example-slug>
- **Goal**: <one sentence, falsifiable>
- **Trigger**: every 7d
- **Next run**: YYYY-MM-DD
- **Observation**: `<shell command>` — returns `<format>`
- **Criterion**: `<expression>` (e.g., `score >= 85`)
- **Brain context**: DECISIONS LOG, RECENT SESSIONS
- **Status**: active

### History
- YYYY-MM-DD SUCCESS <observation snippet> → <action>

### Tuning Log
- YYYY-MM-DD <what changed>. Reason: <why>.

---

> **For Claude**: when running a loop, never invent the observation
> output. If the command fails or the user can't supply a manual
> answer, append `SKIPPED` to history with a reason. When tuning, cite
> at least 3 prior runs in your rationale or refuse to tune.
