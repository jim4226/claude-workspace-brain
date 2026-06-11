---
description: Read-only status of all self-improving loops in WORKSPACE_LOOPS.md — due now, due soon, stable, failing, paused, retired
---

Show every loop in `WORKSPACE_LOOPS.md` at a glance. Read-only — does
not run loops, edit specs, or touch the brain. Use this to triage
before deciding which loop to `/loop-run` or `/loop-tune`.

### Step 1 — read

Read `WORKSPACE_LOOPS.md`. If it doesn't exist:

> "No loops file yet. `/loop-init` creates one."

Stop.

### Step 2 — bucket

Group loops into five buckets (in this order):

| Bucket | Filter |
|--------|--------|
| **Due now** | Status ∈ {active, stable}, Next run ≤ today |
| **Due soon** | Status ∈ {active, stable}, Next run within 3 days |
| **Stable** | Status = stable, not due yet |
| **Failing** | Status ∈ {active}, last 3 runs include ≥ 2 FAILURE or SKIPPED |
| **Paused / retired** | Status ∈ {paused, retired} |

A loop only appears in one bucket — `Due now` wins over `Failing`
when both apply (the user needs to know it's due before they
debate retiring it).

### Step 3 — render

For each non-empty bucket, print a header and one line per loop:

```
DUE NOW (N)
  <slug>  goal: <truncated to 60 chars>  next: <today|YYYY-MM-DD>

DUE SOON (M)
  <slug>  goal: <…>  next: YYYY-MM-DD (in <K> days)

STABLE (K)
  <slug>  streak: <N> SUCCESS  next: YYYY-MM-DD

FAILING (J)
  <slug>  streak: <N> FAILURE  last: YYYY-MM-DD  → /loop-tune suggested

PAUSED / RETIRED (Q)
  <slug>  status: <paused | retired>  retired: YYYY-MM-DD  (kept for history)
```

If a bucket is empty, omit it entirely — silence beats noise here.

### Step 4 — overall summary

End with one line:

```
<TOTAL> loops · <DUE> due · <FAILING> failing · last run anywhere: YYYY-MM-DD
```

If `FAILING > 0`, follow with:

```
Tip: failing loops usually mean the criterion drifted from reality.
     Try /loop-tune <slug> — needs ≥ 3 runs in history.
```

If `DUE NOW > 0`:

```
Tip: /loop-run <slug> runs one. The loop runner (opt-in) emits this
     same list at Stop if you'd rather be reminded.
```

### Notes

- This command is intentionally cheap (no commands executed, no
  network). It should answer "what's the state of my loops?" in under
  a second even with dozens of loops.
- If you want the full History or Tuning Log for one loop, read the
  raw section in `WORKSPACE_LOOPS.md` — that's the source of truth.
