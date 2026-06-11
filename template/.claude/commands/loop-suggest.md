---
description: Read the brain (and research sidecar, if present) and propose 1-3 self-improving loops the project's own state suggests — closes the "loops build by themselves" gap so the user doesn't have to think up loops from scratch
---

The brain already contains the *signal* about which loops would help.
Recurring decisions, watch-flavored open questions, regression patterns
in RECENT SESSIONS, `[pattern]` research insights with implications —
each is a hint that a loop should exist. This command extracts those
hints into concrete loop proposals.

You don't have to know what to ask for. You confirm or reject.

### Hard rule: propose, never apply

`/loop-suggest` writes **nothing** by itself. Every proposed loop must
go through `/loop-init`'s falsifiability gate before it can be created.
This command's only job is to surface candidates with pre-filled
fields you can accept, modify, or reject.

---

### Step 1 — read the inputs

Read every file that exists (skip silently if absent):

1. `WORKSPACE_BRAIN.md` — required. Without a brain, there's no signal.
2. `WORKSPACE_RESEARCH.md` — optional. `[pattern]` insights with
   `→ implication:` clauses are gold-tier loop candidates.
3. `WORKSPACE_LOOPS.md` — optional. Used **only** to avoid proposing
   duplicates of existing loops (active OR retired — don't suggest a
   re-creation of a loop the user already chose to retire).

If `WORKSPACE_BRAIN.md` is missing or empty (still template
placeholders), stop: "Brain has no signal yet. Run `/brain-init` first,
work on the project for a session or two, then come back."

### Step 2 — extract loop-worthy patterns

Walk the brain section-by-section. Each section has its own
loop-worthiness signal:

| Brain section | What to look for | Loop flavor |
|---|---|---|
| `ACTIVE FOCUS` | Mention of a deadline or weekly milestone | **Cadence loop** — check progress weekly |
| `ACTIVE THREADS` | A thread marked `blocked` for >7 days | **Unblock-check loop** — weekly poke at the blocker |
| `DECISIONS LOG` | Decisions citing "every week", "monthly", "regularly", "after each", "before deploys" | **Cadence loop** — automate the check the decision committed you to |
| `SYNAPSES` | Pointers using "check before", "validate", "must come after" | **Validation loop** — automate the pre-flight |
| `KEY NUMBERS` | Numeric targets ("p95 < 200ms", "<= 4 min build", "<32 KB") | **Metric loop** — verify the number still holds |
| `RECENT SESSIONS` | Same issue mentioned in 2+ sessions in the last 30 days | **Regression-watch loop** — catch the pattern before it bites |
| `OPEN QUESTIONS` | Questions with verbs "track", "monitor", "watch", "verify", "audit" | **Watch loop** — until the question is answered, observe the thing |

If `WORKSPACE_RESEARCH.md` is present, also walk it:

| Research entry | What to look for | Loop flavor |
|---|---|---|
| `[pattern]` insight with `→ implication:` | the implication has a measurable effect | **Hypothesis-test loop** — once the implication is shipped, watch the metric the insight predicted |
| Studies older than 6 months still cited in SYNAPSES | Time-bombed assumption | **Re-validation loop** — re-run a small follow-up study yearly |

Each extracted pattern is a candidate.

### Step 3 — score and rank

Score each candidate 1-3 on three axes:

| Axis | 1 | 2 | 3 |
|---|---|---|---|
| **Signal** | one weak hint | two converging hints | three+ converging hints |
| **Falsifiability** | criterion would be hand-wavy | criterion plausible but needs work | criterion writes itself |
| **Brain coupling** | only references one section | references 2-3 sections | naturally cites many sections, would update DECISIONS LOG on tuning |

Total 3-9. Drop anything < 6.

Rank descending. Take the top 3. **If fewer than 3 score ≥ 6, propose
only the ones that do.** Don't pad — a thin proposal is worse than no
proposal.

### Step 4 — pre-fill specs

For each proposed loop, draft the full spec the user would supply to
`/loop-init`:

```
PROPOSAL 1 of N — score X/9

Slug:         <kebab-case derived from the goal>
Goal:         <one sentence; falsifiable; cites the brain section
              that triggered the proposal>
Observation:  <shell command if obvious; else `manual:<question>`>
Criterion:    <expression on the observation parse>
Trigger:      <every Nd | manual; conservative default = manual>
Brain context: <comma-separated sections the loop should consult on tune>
First-failure action: <what to do when the criterion fails>

Why this loop?
  - <brain evidence 1 — quote the section + 1 line>
  - <brain evidence 2>
  - <(if research) [pattern] insight quoted>

Risk: <one sentence — false positives, observation flakiness, drift, etc.>
```

Rules for the pre-fill:

- **Conservative trigger**: default `manual`. The user can promote to
  `every 7d` after one run. Auto-firing a brand-new loop is rude.
- **Concrete observation**: if you can write a shell command, do it.
  If not, use `manual:<question>` — never leave it blank.
- **Falsifiable criterion**: the test is whether `/loop-init` would
  accept it. If it wouldn't, redraft before showing.
- **Cite the brain**: every proposed loop must include "Why this loop?"
  with at least two specific quotes from the brain (or research). No
  generic "would be useful to watch X" — show your work.

### Step 5 — present and gate

Show all N proposals at once. Then ask, one proposal at a time:

> Proposal 1 (score 8/9): create as drafted, modify, or skip?

- **Create as drafted** → invoke the `/loop-init` flow with the
  pre-filled values; the user just confirms each field.
- **Modify** → ask what they'd change, then proceed to `/loop-init`
  with the adjustments.
- **Skip** → record nothing. Don't track skipped proposals — the next
  `/loop-suggest` run is a fresh scan; if the signal is still there it
  will resurface.

If the user creates a loop and the loops file didn't exist, ensure
`WORKSPACE_LOOPS.md` is created with the header (mirror `/loop-init`'s
template). Don't duplicate the header on subsequent creations.

### Step 6 — report

End with exactly this template:

```
Reviewed: brain (<N> sections), research (<M> insights), loops (<K> existing).
Candidates extracted: <total>
Candidates above score threshold: <ranked>
Proposed: <num proposed>
  - <slug 1>: <action: created | modified | skipped>
  - <slug 2>: ...
Created this run: <N>
```

If `created = 0`, end with:

> No loops created. The candidates either weren't a fit or already
> match existing loops. Re-run after another week of work in the brain
> for fresh signal.

If `created >= 1`, end with:

> Created loops won't fire automatically until you set a non-`manual`
> Trigger or run `/loop-run <slug>`. The `--with-loop-runner` and
> `--with-loop-autopilot` install flags control how aggressively due
> loops are surfaced or driven.

### Notes

- This command is **read-mostly**. It reads three files, writes none
  unless the user explicitly approves a `/loop-init` invocation.
- **Don't propose meta-loops on first run.** A "watch the loops file"
  meta-loop is valuable but only after the user has 2-3 real loops to
  watch.
- The 3-proposal cap is intentional. A wall of 12 proposals is a
  worse UX than the user picking from 2-3 well-justified ones.
- If `WORKSPACE_LOOPS.md` contains a `retired` loop matching a fresh
  candidate, **show the retired loop and ask** whether to revive — the
  user may have retired it for a reason that no longer applies.
- Run `/loop-suggest` on roughly the same cadence as `/brain-grade`
  (every 2-4 weeks). New brain signal accumulates; old signal stays
  resolved.
