---
description: Self-improvement step for a loop — analyze the last N runs against the brain's context, propose refinements to goal/criterion/observation/trigger, wait for approval, log the change with rationale
---

This is the **improvement** half of a self-improving loop. `/loop-run`
captures evidence; `/loop-tune` reasons about it and refines the loop
itself. The brain is the substrate for that reasoning: a loop's tuning
decisions are recorded with the same `Reason:` discipline as the brain's
`DECISIONS LOG`, so the improvement record survives compaction.

### Hard rule: cite ≥ 3 prior runs

If `### History` has fewer than 3 entries, refuse to tune and tell the
user:

> "Only <N> run(s) so far — too little evidence. Run the loop a few
> more times, or run `/loop-tune <slug> --force` if you want to ignore
> the rule."

Tuning on N=0 or N=1 is just rewriting the spec, not learning from it.
The 3-run floor mirrors the `[pattern]` threshold from `/user-research`.

---

### Step 1 — load the loop and the brain context

Read `WORKSPACE_LOOPS.md`. Find `## LOOP: <slug>`. If the slug isn't
found, list all available slugs and stop.

Read the brain sections named in the loop's `Brain context` field
(default: `DECISIONS LOG`, `RECENT SESSIONS`). The point is to reason
*from* the brain — what's changed in the project since this loop was
defined? — not from the loop's history in isolation.

### Step 2 — summarize the evidence

Compute and report:

| Stat | What it tells you |
|------|-------------------|
| Total runs | breadth of evidence |
| SUCCESS / FAILURE / SKIPPED counts | rough health |
| Current streak | direction of travel |
| Days since last SUCCESS / FAILURE | recency of either |
| SKIPPED ratio | observation-broken vs criterion-wrong |

Also pull from the brain context: any decisions or sessions in the last
30 days that look relevant to this loop. ("On 2026-05-19 we shipped X;
that may explain why the loop started failing 2026-05-22.")

### Step 3 — diagnose

Pick **one** primary cause from this menu (don't try to diagnose
multiple at once — one tuning per run, like a single decision):

| Cause | Symptom | Typical fix |
|-------|---------|-------------|
| Criterion too tight | streak of FAILUREs, observation values just under the threshold | relax the criterion |
| Criterion too loose | streak of trivial SUCCESSes that don't catch real regressions | tighten the criterion |
| Observation broken | high SKIPPED ratio, recent infra change | rewrite the observation command |
| Goal drift | brain shows the project pivoted; the loop is measuring last quarter's priority | rewrite the goal + criterion |
| Trigger too fast | many runs, low signal per run | back off (`every 7d` → `every 14d`) |
| Trigger too slow | misses windows of failure between runs | tighten frequency or change to `on-session-start` |
| No problem | streak of SUCCESS, criterion still meaningful | promote to `Status: stable`, no spec change |

If none of these fit, say so. Don't pick a cause that doesn't match the
evidence just to have one.

### Step 4 — propose a refinement (don't apply yet)

Show the user **exactly** what you'd change, in diff form:

```diff
- **Criterion**: score >= 90
+ **Criterion**: score >= 85
```

With a `Reason:` clause that cites at least three prior runs by date:

> Reason: 2026-06-04 (78), 2026-05-28 (89), 2026-05-21 (84) — score
> naturally drifts ~5 points between archives; 90 was too tight to
> survive normal slack.

Then ask for approval. Three answers:

1. **Apply as proposed** — proceed to Step 5.
2. **Counter-propose** — user types their own change; you re-validate
   that the change still references the History, then proceed.
3. **Skip** — log the analysis as a tuning-considered entry but don't
   change the spec.

### Step 5 — apply and log

If approved (or counter-proposed):

1. **Edit the loop spec** with the agreed change. One field at a time.
2. **Prepend a Tuning Log entry** with this exact format:
   ```
   - YYYY-MM-DD <one-line change description>. Reason: <citation of
     ≥3 prior runs or brain entries>.
   ```
3. **Mirror to the brain's DECISIONS LOG** (one entry) — tuning a loop
   is a project decision and belongs in the durable record:
   ```
   - **YYYY-MM-DD**: Tuned loop <slug>: <one-line change>. Reason:
     <citation>. See WORKSPACE_LOOPS.md for full tuning log.
   ```
   The brain's lint axis `Decision rationale` will catch any tuning
   without a `Reason:` — that's the gate by design.

If skipped:

- Append a tuning-considered entry to the Tuning Log:
  ```
  - YYYY-MM-DD Considered tuning; no change applied. Reason: <user
    rationale>.
  ```
- Do not touch the brain.

### Step 6 — report

End with exactly this template:

```
Loop:        <slug>
Action:      <APPLIED | COUNTER-APPLIED | SKIPPED>
Change:      <one-line summary, or "none">
Reason:      <citation>
Mirrored to brain DECISIONS LOG: <yes | no>
Next run:    <date or "manual">
History length now: <N>  (tuning floor was 3)
```

### When to use `--force`

Pass `--force` to bypass the 3-run minimum. Legitimate uses:

- The observation is clearly wrong (e.g., command not found) — fix it
  immediately rather than letting it SKIP three times.
- The project just pivoted; the goal is stale and you need to update
  before the next run produces noise.

Document the `--force` reason in the Tuning Log entry. The brain
mirror still happens.

### Notes

- **One tuning per run.** Cumulative tuning across many fields at once
  destroys the cause-and-effect of the spec. Tune one field, see what
  happens over the next 2-3 runs, tune again if needed.
- **Retiring a loop** is a tune like any other (`Status: retired`).
  Don't delete retired loops — their History is part of the project's
  memory.
- **Meta-loops are allowed.** A loop that watches `WORKSPACE_LOOPS.md`
  for stale loops (last run > 60d) is a perfectly valid self-monitoring
  pattern. `/loop-init` accepts an observation that points at the loops
  file.
