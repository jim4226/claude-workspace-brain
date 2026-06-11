---
description: Execute one named self-improving loop — run its observation, evaluate the criterion, append to history, gate brain edits, escalate on repeated failure
---

Run a loop defined in `WORKSPACE_LOOPS.md` exactly once. This command
does the four things a single loop iteration must do:

1. **Observe** — execute the loop's observation (a shell command or
   `manual:` prompt). Never invent the output.
2. **Judge** — evaluate the criterion against the observation. If the
   criterion can't be parsed, append `SKIPPED` to history and stop.
3. **Record** — append a new History entry (date · status · observation
   snippet · action). History is append-only.
4. **Escalate** — on consecutive failures (3+), prepend a "Reconsidering"
   entry to the brain's `OPEN QUESTIONS` and suggest `/loop-tune`.

### Hard rule: never fabricate a run

If the observation command fails, hangs, or returns no parseable output,
the run is `SKIPPED`, not `SUCCESS`/`FAILURE`. If the user is unavailable
for a `manual:` observation, also `SKIPPED`. The History log is evidence;
it can only contain things that actually happened.

---

### Step 1 — locate the loop

The slug is passed in the command args (or asked for if missing). Read
`WORKSPACE_LOOPS.md` and find the `## LOOP: <slug>` section.

- If `WORKSPACE_LOOPS.md` doesn't exist: "No loops file yet — try
  `/loop-init` to create one." Stop.
- If the slug isn't found: list all available slugs from the file.
  Don't fuzzy-match silently. Stop.
- If the loop's `Status` is `paused` or `retired`: refuse, with the
  hint "use `/loop-tune <slug>` to reactivate".

### Step 2 — execute the observation

If the observation is a shell command:

```bash
<command>
```

Capture exit code + stdout. Report both to the user verbatim — they need
to see what actually came back.

If the observation is `manual:<question>`, ask the user the question
exactly as written. Wait for the answer. Don't paraphrase.

### Step 3 — evaluate the criterion

The criterion is a Python-style boolean expression on one variable
extracted from the observation (e.g., `score >= 85`). Two evaluation
modes:

| Observation type | Variable | Extraction |
|------------------|----------|------------|
| Shell command | `exit_code` | from the run |
| Shell command | `count` | number of non-empty lines in stdout |
| Shell command | `score` / `value` / custom | regex extract from stdout (the loop spec should hint at the pattern; if not, ask) |
| `manual:` | `answer` | the user's reply, coerced to int / yes-no as appropriate |

If the criterion can't be evaluated against the observation (e.g.,
spec says `score >= 85` but the command produced no number), append
`SKIPPED reason=<reason>` to History and stop. Do **not** guess at the
value. Suggest the user run `/loop-tune <slug>` to fix the observation.

### Step 4 — record the run

Append to the loop's `### History` section (newest first). Format:

```
- YYYY-MM-DD SUCCESS <snippet> → <action>
- YYYY-MM-DD FAILURE <snippet> → <action>
- YYYY-MM-DD SKIPPED <snippet> → reason: <reason>
```

Rules:

- `<snippet>` ≤ 60 chars. The full observation can go in a referenced
  log if needed, but the History is a one-liner.
- `<action>`: on success, normally "noted". On failure, run the loop's
  `First-failure action` and note it (e.g. "→ suggested /brain-archive").
  Don't actually run other slash commands without user approval; suggest
  them.
- **Don't edit any prior History entry.** Append only.

Also update the loop's `Next run` field per its `Trigger`:

| Trigger | Next-run update |
|---------|-----------------|
| `every Nd` | today + N |
| `manual` | leave as `manual` |
| `on-session-start` | leave (handled by SessionStart hook) |

### Step 5 — promote to `stable` (success) or escalate (failure)

Count consecutive runs from the top of `### History`:

- **5+ consecutive SUCCESS** and current Status is `active` → set
  `Status: stable`. Optionally double the trigger interval (e.g.
  `every 7d` → `every 14d`); ask the user before doing so.
- **3+ consecutive FAILURE** → prepend to `WORKSPACE_BRAIN.md`
  `OPEN QUESTIONS`:
  ```
  Reconsidering loop <slug> — 3+ consecutive failures (triggered by
  WORKSPACE_LOOPS.md). Run /loop-tune <slug> to refine criterion or
  observation, or pause/retire the loop.
  ```
  Surface this to the user explicitly — a loop that keeps failing
  silently is worse than no loop.
- **SKIPPED ≥ 3 in last 5 runs** → suggest `/loop-tune <slug>` to fix
  the observation. Don't escalate to OPEN QUESTIONS; this is a tooling
  problem, not a signal.

### Step 6 — report

End with exactly this template:

```
Loop:        <slug>
Run:         <SUCCESS | FAILURE | SKIPPED>
Observation: <snippet>
Criterion:   <expression> → <evaluated result>
Action:      <what you did or suggested>
Next run:    <new next-run value>
Status:      <active | stable | paused | retired> (was <prev> if changed)
Streak:      <N> consecutive <SUCCESS | FAILURE>
```

If the run was a FAILURE that escalated to OPEN QUESTIONS, add:

```
⚠️  Escalated: WORKSPACE_BRAIN.md OPEN QUESTIONS updated. Consider
    /loop-tune <slug> before the next scheduled run.
```

### Notes

- Loops can be run any time, not just when due. `/loop-run <slug>`
  bypasses the Next-run gate.
- A loop run does **not** modify `DECISIONS LOG` directly — only
  `/loop-tune` does, because tuning is a decision worth preserving.
- If the observation command requires permissions Claude doesn't have,
  the run is SKIPPED with reason `permission`. The user can re-run
  with the permission granted.
