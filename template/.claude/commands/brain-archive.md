---
description: Migrate stale completed threads + old sessions to WORKSPACE_BRAIN_ARCHIVE.md
---

Keep `WORKSPACE_BRAIN.md` lean by moving aged-out content to a sidecar archive.
The active brain stays small (fast to inject); the archive preserves history
without bloating every session.

### Step 1 — survey

Read `WORKSPACE_BRAIN.md` and identify:

- **Completed threads** in `ACTIVE THREADS` marked `(done)`, `[x]`, or a check.
  Anything older than 14 days is a strong archive candidate.
- **Sessions** in `RECENT SESSIONS` beyond the 10 newest entries.
- **Decisions** in `DECISIONS LOG` older than 90 days that aren't load-bearing
  for current decisions (skim the SYNAPSES section to check for references).
- **Resolved open questions** — these should already be removed when answered;
  flag any that look stale (>30 days old, no recent activity nearby).

Report a preview to the user: "I propose to move <N> threads, <M> sessions,
and <K> decisions to archive. Total: ~<X> lines, ~<Y> KB."

### Step 2 — wait for approval

Do not edit anything yet. Ask the user one of:
1. "Apply the migration as proposed?"
2. "Adjust the cutoff? (default: 14d threads / 10 sessions / 90d decisions)"
3. "Skip - cancel."

Wait for their answer.

### Step 3 — execute the migration

If approved:

1. If `WORKSPACE_BRAIN_ARCHIVE.md` doesn't exist, create it with the header:
   ```
   # WORKSPACE BRAIN — Archive
   > Aged-out entries from WORKSPACE_BRAIN.md. Not auto-injected.
   > Append-only; oldest at bottom.
   ```
   Use **Write** for creation. Otherwise use **Edit** to insert at the top
   (newest archived first).

2. For each archived entry, **prepend** to the archive under a date-stamped
   section: `## Archived 2026-MM-DD`, then the entries grouped by their
   original section name (`### From ACTIVE THREADS`, etc.).

3. **Remove** the same entries from `WORKSPACE_BRAIN.md` using **Edit**.

### Step 4 — verify

Run the linter on the trimmed brain:

```bash
python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md
```

Report the new size + score. The archive operation should improve the
**size budget** axis. Don't proceed if the brain ends up with an empty
required section — restore those entries and warn the user.

### Step 5 — summary

End with one line:

> Archived <N> entries. Brain size: <before> KB -> <after> KB.
> Lint score: <before>/100 -> <after>/100.
