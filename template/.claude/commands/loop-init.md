---
description: Factory for self-improving loops backed by the workspace brain — interactively define a goal, observation, success criterion, and brain context, then write a well-formed entry to WORKSPACE_LOOPS.md
---

A **loop** is a recurring check that defines, runs, and improves itself.
It rides on the workspace brain: its history survives compaction, its
tuning decisions are append-only with rationale (like `DECISIONS LOG`),
and it reads brain sections for context. The brain provides the memory
that turns a one-shot task into a learning system.

This command is the **factory**: it takes a goal and produces a
well-formed loop specification. After this, `/loop-run` executes it,
`/loop-tune` improves it, and `/loop` shows status.

### Hard rule: a loop must be falsifiable

If the user can't state a success criterion you could check
mechanically, **stop and ask for one**. A loop with `criterion:
"things feel right"` is unfixable — the runner cannot judge
success, the tuner cannot reason about failure. Better to refuse
the loop than ship a vague one.

Acceptable criteria:
- `score >= 85` (parsed from a linter)
- `exit_code == 0` (command ran cleanly)
- `count == 0` (no items match a pattern)
- `delta <= 2` (a metric stayed within a band)
- `<user-supplied boolean>` (manual mode — user answers yes/no)

Unacceptable: anything that requires Claude or the user to *feel* the
answer.

---

### Step 1 — clarify the loop's intent

Use `AskUserQuestion` if available. Ask all of these — in this order
(each later answer constrains the earlier ones, so don't skip):

1. **Slug** — short kebab-case identifier, e.g.
   `brain-grade-weekly`, `staging-uptime-daily`. Used in
   `/loop-run <slug>`. Must be unique in `WORKSPACE_LOOPS.md`.
2. **Goal** — one sentence describing what the loop is preserving or
   improving. Falsifiable.
3. **Observation** — how do we measure it? Either:
   - a shell command (its stdout is the observable), OR
   - `manual:<question>` — runner asks the user, user answers yes/no
     or supplies a number.
4. **Criterion** — the boolean that defines success on the observation.
5. **Trigger** — `every <N>d`, `manual`, or `on-session-start`.
   Default `manual` for the first loop; users should opt into automatic
   triggers after they see a loop work.
6. **Brain context** — which `WORKSPACE_BRAIN.md` sections should
   `/loop-tune` read when reasoning about this loop? Comma-separated
   list. Default: `DECISIONS LOG, RECENT SESSIONS`.
7. **First-failure action** — what should happen if the criterion fails?
   Free text — gets recorded in the loop spec and surfaced to the user
   on every failure. Examples: "run /brain-archive", "open an issue",
   "ask me to triage".

If any answer is vague, **push back once**: "That criterion isn't
mechanically checkable — can you restate as `<concrete expression>`?"
After one push-back, accept the user's version and proceed — over-gating
the factory will frustrate first-time users.

### Step 2 — check for collisions

Read `WORKSPACE_LOOPS.md` (create it from
`template/WORKSPACE_LOOPS.md` if missing). Scan for an existing
`## LOOP: <slug>` section.

- If a loop with the same slug exists and is `retired`: refuse and
  suggest a new slug.
- If it exists and is `active` / `stable` / `paused`: refuse and offer
  `/loop-tune <slug>` to refine the existing one.

### Step 3 — sanity-check the observation

If the observation is a shell command, **run it once** in dry-run mode to
confirm it actually produces output the criterion can parse against:

```bash
# example
python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md | grep -oE 'Score: [0-9]+'
```

Report what came out. If parsing the criterion against this output isn't
obvious, ask the user how to extract the value. Don't assume.

If the observation is `manual:<question>`, skip this step.

### Step 4 — write the loop spec

Use **Edit** (or **Write** if creating the file). Append a new
`## LOOP: <slug>` section to `WORKSPACE_LOOPS.md` with this exact
structure (the linter checks for these fields):

```markdown
## LOOP: <slug>
- **Goal**: <one sentence>
- **Trigger**: <every Nd | manual | on-session-start>
- **Next run**: <YYYY-MM-DD | manual>
- **Observation**: `<command>` — returns <format>
- **Criterion**: `<expression>`
- **Brain context**: <comma-separated sections>
- **First-failure action**: <free text>
- **Status**: active

### History
*(append-only, newest first; YYYY-MM-DD STATUS snippet → action)*

### Tuning Log
*(append-only; YYYY-MM-DD change. Reason: why.)*
- <today>: Loop created via /loop-init. Reason: <Goal>.
```

Notes:

- **Next run**: if trigger is `every Nd`, set today + N. If `manual`,
  set `manual`. Never invent dates.
- **Status** starts at `active`. `/loop-run` may promote to `stable`
  after 5 consecutive successes.
- The first `Tuning Log` entry is the creation note. It cites the
  Goal as the reason so the linter's `Reason:` check passes from day one.

### Step 5 — wire to the brain

Add a single `SYNAPSES` entry to `WORKSPACE_BRAIN.md` the first time
`WORKSPACE_LOOPS.md` gets created:

```
- **WORKSPACE_LOOPS.md** <-> **<topic>** — self-improving loops; consult
  before changing related code
```

(Topic = whatever area the first loop watches. Use the loop's slug if
unclear.) Don't re-add on subsequent loop creations.

### Step 6 — report

End with:

```
Loop created: <slug>
  Goal:        <goal>
  Trigger:     <trigger>  (next: <next-run>)
  Observation: <command-snippet>
  Criterion:   <expression>

Next steps:
  - Run it now:   /loop-run <slug>
  - Tune later:   /loop-tune <slug>
  - See all:      /loop

The loop's history is append-only — every run, every tuning decision,
every failure becomes part of the brain's long-term memory. Improvement
compounds across sessions.
```

If the SYNAPSES entry was added, mention it: `Added SYNAPSES pointer:
WORKSPACE_LOOPS.md <-> <topic>.`

### Notes

- See `examples/loops-walkthrough.md` for a worked example: a
  brain-health loop that fails, self-tunes, then succeeds.
- **Three trigger modes**, increasing in autonomy:
  - **`brain_loop_runner.py`** (opt-in, `--with-loop-runner`) —
    *surfaces* due loops with a one-line directive each Stop. You
    still manually run `/loop-run <slug>`. Best for "I want a nudge".
  - **`brain_loop_autopilot.py`** (opt-in, `--with-loop-autopilot`) —
    *drives* due loops by blocking the stop and asking Claude to
    invoke `/loop-run <slug>`. Budget-bounded (default: max 2 blocks
    per session, max 1 per loop per session); anti-spin guard (no
    block if last block produced no new History entry); kill switch
    `BRAIN_LOOPS_OFF=1`. Best for "I want it just to happen".
  - **Neither** (default) — loops only run when you ask. Best for
    first-time users.
- Loops can be run with `/loop-run` regardless of trigger mode. The
  hooks only control when the *next* run is prompted.
- Loops are **not** the right tool for one-shot tasks. If you only ever
  need the answer once, just ask Claude directly.
- A loop is itself a hypothesis. Expect to tune it. Loops that never
  need tuning either watch a triviality or aren't really watching
  anything.
