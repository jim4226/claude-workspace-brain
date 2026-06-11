# Self-improving loops — a fully worked example

This walks through one realistic loop end-to-end: define → run → fail →
escalate → self-tune → succeed → stabilize. The point is to show how the
brain's persistence turns a one-shot check into a learning system.

## The premise

You ship code, the brain grows, the brain rots. You'd like a recurring
check that catches rot before it bites — but you don't want to *manually*
remember to run it. You also don't want a check that lies to you because
it was poorly defined six months ago. You want a loop that watches itself.

## Day 0 — define the loop

```
> /loop-init
```

Claude asks the six factory questions. Your answers:

| Q | Answer |
|---|--------|
| Slug | `brain-grade-weekly` |
| Goal | "Keep brain lint score ≥ 90 — catch decay before sessions start losing context" |
| Observation | `python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md` |
| Criterion | `score >= 90` |
| Trigger | `every 7d` |
| Brain context | `DECISIONS LOG, RECENT SESSIONS` |
| First-failure action | "Open a TODO to run /brain-archive within 48h" |

Claude runs the observation once dry to confirm it parses:

```bash
$ python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md | grep -oE 'Score: [0-9]+'
Score: 91
```

Then writes a new section to `WORKSPACE_LOOPS.md`:

```markdown
## LOOP: brain-grade-weekly
- **Goal**: Keep brain lint score ≥ 90 — catch decay before sessions
  start losing context
- **Trigger**: every 7d
- **Next run**: 2026-06-18
- **Observation**: `python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md` — returns score on stdout
- **Criterion**: `score >= 90`
- **Brain context**: DECISIONS LOG, RECENT SESSIONS
- **First-failure action**: Open a TODO to run /brain-archive within 48h
- **Status**: active

### History

### Tuning Log
- 2026-06-11 Loop created via /loop-init. Reason: Keep brain lint score ≥ 90 — catch decay before sessions start losing context.
```

And a SYNAPSES entry in the brain (first time the loops file gets a topic):

```
- **WORKSPACE_LOOPS.md** <-> **brain hygiene** — self-improving loops;
  consult before changing related code
```

Report:

```
Loop created: brain-grade-weekly
  Goal:        Keep brain lint score ≥ 90 …
  Trigger:     every 7d  (next: 2026-06-18)
  Observation: python .claude/scripts/brain_lint.py …
  Criterion:   score >= 90

Next steps:
  - Run it now:   /loop-run brain-grade-weekly
  - Tune later:   /loop-tune brain-grade-weekly
  - See all:      /loop
```

## Day 7 — first run, fails

The SessionStart breadcrumb tells you the loop is due:

> (Adjacent: WORKSPACE_LOOPS.md — 1 self-improving loop(s), 1 due. Run
> /loop for status or /loop-run <slug> to act.)

You ask Claude to run it.

```
> /loop-run brain-grade-weekly
```

Claude executes the observation:

```
$ python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md
Score: 87
```

Evaluates the criterion: `87 >= 90` → **FAILURE**. Appends to History:

```markdown
### History
- 2026-06-18 FAILURE score=87 → suggested running /brain-archive
```

Updates Next run to `2026-06-25`. Reports:

```
Loop:        brain-grade-weekly
Run:         FAILURE
Observation: Score: 87
Criterion:   score >= 90 → False
Action:      Suggested running /brain-archive (per First-failure action).
Next run:    2026-06-25
Status:      active
Streak:      1 consecutive FAILURE
```

You don't act on the suggestion immediately — your sprint is busy.

## Days 14 and 21 — second and third failures

Two more weekly runs, two more failures (88 and 86). After the third,
Claude does the **escalation**:

```markdown
# in WORKSPACE_BRAIN.md OPEN QUESTIONS
- Reconsidering loop brain-grade-weekly — 3+ consecutive failures
  (triggered by WORKSPACE_LOOPS.md). Run /loop-tune brain-grade-weekly
  to refine criterion or observation, or pause/retire the loop.
```

And the report ends with:

```
⚠️  Escalated: WORKSPACE_BRAIN.md OPEN QUESTIONS updated. Consider
    /loop-tune brain-grade-weekly before the next scheduled run.
```

A loop that quietly keeps failing is worse than no loop. The brain's
OPEN QUESTIONS now forces a conversation.

## Day 22 — self-improvement via `/loop-tune`

```
> /loop-tune brain-grade-weekly
```

Claude reads the loop section and the brain sections it cites
(`DECISIONS LOG`, `RECENT SESSIONS`). It produces a diagnosis:

> **Evidence**:
> - 3 runs, 0 SUCCESS / 3 FAILURE / 0 SKIPPED.
> - Scores: 87, 88, 86 — all in the 85–88 band.
> - Brain `RECENT SESSIONS` shows a sustained push on feature work; no
>   archive runs in the last 30d.
> - Brain `DECISIONS LOG` from 2026-05-12 noted "Storybook dropped, 90%
>   of decisions logged with rationale" — implying the rationale axis
>   should stay perfect, but the size budget axis will drift unless
>   `/brain-archive` runs.
>
> **Diagnosis**: Criterion too tight. The scores cluster at 85–88; 90
> was an aspirational threshold that the natural drift between archive
> runs doesn't survive. Two fixes:
> - Relax to `score >= 85` — accepts the drift, still catches real rot
>   below 85.
> - **OR** keep the threshold and add an action: auto-suggest
>   `/brain-archive` on any score 85-89 (already happens; not enough).
>
> Recommend the first — the threshold was aspirational, not empirical.
>
> **Proposed change** (one field):
>
> ```diff
> - **Criterion**: `score >= 90`
> + **Criterion**: `score >= 85`
> ```
>
> Reason: 2026-07-09 (86), 2026-07-02 (88), 2026-06-25 (87) — three
> runs in the 85-88 band. The 90 threshold predicts failure on every
> natural between-archive sample. 85 leaves real headroom for actual
> rot (sub-85) while accepting normal drift.
>
> Apply / counter-propose / skip?

You: **apply**.

Claude:
1. Edits the loop's `Criterion` field.
2. Prepends to the loop's Tuning Log:
   ```
   - 2026-07-09 Relaxed criterion from `score >= 90` to `score >= 85`.
     Reason: 2026-07-09 (86), 2026-07-02 (88), 2026-06-25 (87) — three
     runs in the 85-88 band; 90 was aspirational, not empirical.
   ```
3. Mirrors to the brain's DECISIONS LOG:
   ```
   - **2026-07-09**: Tuned loop brain-grade-weekly: relaxed criterion
     from `score >= 90` to `score >= 85`. Reason: 3-run history (87,
     88, 86) clusters in the 85-88 band. See WORKSPACE_LOOPS.md.
   ```
4. The brain's `Reason:` linter axis stays happy — every tuning is a
   decision, every decision has rationale.

## Days 29 → 57 — five successes, promoted to stable

The next four weeks pass without incident:

```markdown
- 2026-08-06 SUCCESS score=88 → noted
- 2026-07-30 SUCCESS score=86 → noted
- 2026-07-23 SUCCESS score=89 → noted
- 2026-07-16 SUCCESS score=87 → noted
- 2026-07-09 FAILURE score=86 → tuned (see Tuning Log)
- 2026-07-02 FAILURE score=88 → suggested /brain-archive
- 2026-06-25 FAILURE score=87 → escalated to OPEN QUESTIONS
- 2026-06-18 FAILURE score=87 → suggested /brain-archive
```

After 4 consecutive SUCCESSes (since the tune), Claude asks (it needs 5
for stable, plus your approval to slow the trigger):

```
Loop brain-grade-weekly has 4 consecutive SUCCESS runs since the
2026-07-09 tune. One more SUCCESS will trigger a `Status: stable`
promotion. Want me to also slow the trigger from every 7d to every
14d at that point? (Stable loops still run, just less often.)
```

You: **yes**. On the next SUCCESS (Day 57), Claude:

```diff
- **Trigger**: every 7d
+ **Trigger**: every 14d
- **Status**: active
+ **Status**: stable
```

With another Tuning Log entry + DECISIONS LOG mirror.

## Day 60 — the meta-loop

You're now confident enough to add a **loop that watches the loops**:

```
> /loop-init

Slug:        loops-staleness-monthly
Goal:        Catch loops that haven't run in 60d — they're either
             retiring themselves through neglect or the trigger is wrong
Observation: grep -c "^- 2026-" WORKSPACE_LOOPS.md | head -1
Criterion:   <user fills out a manual checker — too complex for a one-liner>
Trigger:     every 30d
Brain context: DECISIONS LOG
First-failure action: ask me to review each stale loop
```

(In practice the observation here would be `manual:Are any loops in
WORKSPACE_LOOPS.md older than 60 days?` — manual mode is fine and you
answer yes/no. The point is *the loop file itself* is now monitored.)

You now have a small self-running, self-improving, self-monitoring
system. The brain is the substrate; the loops are the discipline.

## What you'd see in the brain after all this

```markdown
## DECISIONS LOG
- **2026-08-06**: Promoted loop brain-grade-weekly to `stable`,
  trigger every 14d. Reason: 5 consecutive SUCCESS runs since the
  2026-07-09 tune.
- **2026-07-09**: Tuned loop brain-grade-weekly: relaxed criterion
  from `score >= 90` to `score >= 85`. Reason: 3-run history (87,
  88, 86) clusters in the 85-88 band. See WORKSPACE_LOOPS.md.
- … (older decisions)

## SYNAPSES
- **WORKSPACE_LOOPS.md** <-> **brain hygiene** — self-improving loops;
  consult before changing related code
- … (older synapses)
```

Compaction can come and go. The loops keep their History. The brain
keeps the rationale for every tuning. Six months from now, when a new
maintainer wonders "why is the lint threshold 85 and not 90?", the
record is right there.

## Autopilot mode — making the loop run itself

The walkthrough above had you manually invoke `/loop-run` each week.
That's the conservative default. If you'd rather the loop **just
happen**, install with `--with-loop-autopilot`:

```bash
python _install.py --target . --yes --with-loop-autopilot
```

Now what happens on a Stop event (i.e. when Claude finishes a reply)
with a due loop and no recent autopilot activity:

```
> "thanks, that's all for today"
[Claude's reply ends]

[brain_loop_autopilot.py fires]
[autopilot sees brain-grade-weekly is due, history=4, last block in this
 session was at history=4 too? No — fresh session, no prior block]
[emits {"decision": "block", "reason": "...Loop autopilot-test is due..."}]

[Claude Code blocks the stop, hands the directive to Claude]
[Claude: "Right — autopilot is driving the brain-grade-weekly loop.
          Running /loop-run brain-grade-weekly now..."]
[Score: 89. Criterion 85 met. History entry appended. Next run += 7d.]

[Claude tries to stop again]
[autopilot fires; history is now 5 (grew by 1); per-loop budget is 1;
 this session already had 1 block for this loop → allow stop]
[Session ends naturally]
```

Four guards keep this from running away:

| Guard | Default | Purpose |
|-------|---------|---------|
| Kill switch | `BRAIN_LOOPS_OFF=1` | Master off — set it in your shell to silence all autopilot for the session |
| Session-wide block cap | 2 | Total autopilot blocks per session — even across multiple loops |
| Per-loop session cap | 1 | One iteration of any given loop per session |
| Anti-spin | always on | If History didn't grow between blocks for the same loop in the same session, allow the stop — prevents infinite loops when /loop-run is broken |

The anti-spin guard is the important one. If the observation command
exits non-zero, or Claude SKIPs the run, or the History parser breaks,
the autopilot detects "no progress" on the next Stop and gracefully
hands the session back. You never get a runaway loop — the worst case
is one wasted Stop block.

The autopilot is **opt-in for a reason**: it changes how a session
ends. First-time users should run `--with-loop-runner` (which only
*surfaces* due loops) and graduate to `--with-loop-autopilot` once
they trust their loops' observations.

## What did *not* happen (and why)

- **The Day-7 failure was not silently retried.** The first-failure
  action was logged and the user was informed. Loops that fail
  quietly accumulate noise.
- **Claude did not auto-tune at Day 21.** Escalation went to OPEN
  QUESTIONS, not into a spec change. Tuning requires user approval
  because it changes the rules of the game.
- **The Day-22 tune cited 3 prior runs.** The `/loop-tune` floor is
  3 for a reason — tuning on N=1 is just rewriting the spec, not
  learning from it.
- **The DECISIONS LOG entry for the tune included `Reason:`.** The
  brain's existing `Decision rationale` lint axis catches any tune
  that tries to skip rationale.
- **No History entry was ever edited.** Append-only. The 87/88/86
  scores from days 7-21 stay there as evidence forever.

## Loop anatomy — one-page reference

```
┌────────────────────────────────────────────────────────────────────┐
│  WORKSPACE_LOOPS.md (sidecar; not auto-injected)                   │
│                                                                    │
│  ## LOOP: <slug>                                                   │
│    Spec fields ────────────────┐                                   │
│      Goal / Trigger / Obs /    │   ◄── edited by /loop-tune only   │
│      Criterion / Status        │       (with brain decision-mirror)│
│                                │                                   │
│    ### History (append-only) ──┘   ◄── written by /loop-run only   │
│      one line per run                                              │
│                                                                    │
│    ### Tuning Log (append-only) ◄── written by /loop-init and      │
│      one line per tune              /loop-tune; Reason: required   │
└────────────────────────────────────────────────────────────────────┘

         ▲                                              ▲
         │ surfaces due loops at SessionStart           │
         │ (count + breakdown)                          │
         │                                              │
  brain_session_start.py                          brain_loop_runner.py
  (always-on)                                     (opt-in Stop hook)
                                                  emits LOOPS DUE
                                                  directive once
                                                  per quiet window
```
