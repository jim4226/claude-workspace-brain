---
description: Evaluate WORKSPACE_BRAIN.md quality and suggest concrete edits
---

You are reviewing the brain file for quality. Do this:

### Step 1 — run the static linter

```bash
python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md
```

Report the score and the top 3 findings verbatim.

### Step 2 — read the brain and grade it on five axes (0-10 each)

Then read `WORKSPACE_BRAIN.md` yourself and grade:

1. **Freshness** — When was each section last meaningfully updated? Stale
   threads at the top are worse than stale entries at the bottom.
2. **Signal-to-noise** — Does every line carry weight, or is there filler
   that future-Claude will skim past?
3. **Specificity** — Are decisions and threads concrete (named files,
   dates, owners), or vague ("improve UX", "fix the auth thing")?
4. **Reason coverage** — Do decisions explain *why* (not just *what*)?
   A decision without a reason rots in two weeks.
5. **Section balance** — Is one section dominating? Are required sections
   empty? Should anything be archived?

For each axis: score 0-10, one-line justification, one concrete suggestion.

### Step 3 — propose specific edits

Pick the 1-3 highest-leverage edits (entries to remove, rewrite, or move
to archive). Show the exact Edit-tool calls you'd make. Wait for my
approval before applying any of them.

### Step 4 — overall verdict

End with one line: `Brain quality: <score>/100. <One-sentence recommendation>.`
