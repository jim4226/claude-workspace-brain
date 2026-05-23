# WORKSPACE BRAIN
> Auto-injected at session start. Updated before any context compaction.
> Last sync: YYYY-MM-DD · Maintainer: Claude (with you)

This file is the persistent memory of the workspace. It survives context compaction. Treat its contents as ground truth for what is currently true, in-flight, and decided.

The rules of this file:
1. Be terse. Every line you don't write is a line Claude doesn't have to parse next session.
2. Prefer specifics over generalities ("Stripe webhook signing on staging is broken" beats "auth issues").
3. Include the **why**, not just the **what**. Decisions without reasoning rot fast.
4. Skip anything derivable from code, git log, or CLAUDE.md.
5. When a thread completes, mark it done and let it sink to the bottom — don't delete history.

---

## ACTIVE FOCUS

<!--
One paragraph. What is the user trying to accomplish right now?
This is what Claude should orient around when the user gives a vague request.
-->

**Current goal**: <One sentence describing the overarching project goal.>

**Current sprint**: <One paragraph describing what's being shipped this week / cycle. Be specific — milestones, deadlines, who's waiting.>

**Next on deck**: <What comes after the current sprint, if known.>

---

## ACTIVE THREADS
*(in-flight work, newest commitment first — flip to done when complete)*

<!--
Each line is one piece of work, with a status, a one-line summary, and
optionally the date you committed to it. Use any markers you like for
status; common: pending / in-progress / done / blocked / paused.

When something completes, mark it done and move it toward the bottom.
Don't delete — the completion record helps Claude know what's recent.
-->

- (pending) <Thread description> (YYYY-MM-DD)
- (in-progress) <Thread description> (YYYY-MM-DD)
- (done) <Thread description> (YYYY-MM-DD)

---

## DECISIONS LOG
*(prepend new decisions; format: `- **YYYY-MM-DD**: <decision>. Reason: <why>.`)*

<!--
This is the most valuable section for future-you. It captures judgment
calls that aren't visible in the code: why a particular library was
chosen, why a deadline shifted, why a feature was cut.

The Reason: clause is required. A decision without rationale is just
trivia.
-->

- **YYYY-MM-DD**: <Decision>. Reason: <Why>.

---

## SYNAPSES
*(cross-references between parts of the system — A <-> B)*

<!--
Non-obvious dependencies. When you change file X, you probably need to
remember Y. When metric M moves, dashboard D will alert. These pointers
save Claude from having to rediscover them every session.
-->

- **<thing A>** <-> **<thing B>** — <how they're connected>

---

## KEY NUMBERS
*(metrics, dimensions, dates worth freezing)*

<!--
Stable facts that don't deserve a section of their own but get asked
about repeatedly. Examples: production URL, current benchmark, dataset
size, deadline date, free-tier quota.
-->

- **<name>**: <value> (<as of YYYY-MM-DD>)

---

## RECENT SESSIONS
*(prepend; keep ~10 entries, archive the rest to WORKSPACE_BRAIN_ARCHIVE.md)*

<!--
One line per session: date, what was worked on, what shipped or
unblocked. This is how Claude reconstructs "what did we just do last
time" without re-reading the transcript.
-->

- **YYYY-MM-DD**: <One-line session summary.>

---

## OPEN QUESTIONS
*(things still unresolved — flush when answered)*

<!--
A short list of unresolved questions. When the user resolves one, move
the answer to DECISIONS LOG and delete the question.
-->

- <Open question>

---

> **For Claude**: Update this file before context compaction (the PreCompact hook
> will remind you). Use the Edit tool — never rewrite the whole file.
> Run `/brain-grade` periodically to check quality and surface stale entries.
