# /user-research walkthrough — a fully worked example

This walks through one realistic run of `/user-research describe` end to
end: input → sidecar entry → brain cross-references → report. Use it as a
reference when reviewing how the command should behave.

## Setup

Project state before the command runs (excerpts from `WORKSPACE_BRAIN.md`):

```markdown
## ACTIVE THREADS
- (in-progress) #432 Stripe webhook signing — branch `feat/stripe-signing`, ~80%
- (in-progress) #401 Checkout flow polish — sprint goal, lots of small fixes

## DECISIONS LOG
- **2026-05-19**: Show shipping cost on checkout step 3 (cart confirmation).
  Reason: avoids surprise charges; matches Shopify-style flow we benchmarked.

## OPEN QUESTIONS
- Is the checkout flow's shipping placement the right one for SMB customers?
```

No `WORKSPACE_RESEARCH.md` exists yet. No `./research/` directory yet.

## User input

```
/user-research describe

I just ran 5 30-min remote interviews with SMB founders we recruited via
UserInterviews.com. P01-P05. The study slug is 2026-05-22-checkout-interviews.

Three of them (P01, P03, P05) abandoned a test checkout when they discovered
shipping cost at step 3 — two said variants of "I closed the tab when I saw
the cost". One (P02) asked whether we'd import customers from QuickBooks
(couldn't find the option). P04 was positive overall, no major issues.

I don't have a pseudonym ledger file yet; I keep them in a Notion doc.
```

## Claude's run

**Step 1 — provenance gate.** Checks for `./research/pseudonyms.local.md`:

```
$ test -f ./research/pseudonyms.local.md && echo found || echo missing
missing
```

Asks: "Create a stub now, paste mapping inline, or proceed with
`(no ledger)` ad-hoc IDs (recommended only for first use)?" User
says: "create the stub, I'll mirror it from Notion later."

```
$ mkdir -p ./research && touch ./research/pseudonyms.local.md
```

Reminds the user: add `research/*.local.md` to `.gitignore` if not present.

**Step 2 — extract atomic insights.** Five participants, three confirming
the shipping pattern, one with a QuickBooks comment, one with no signal:

- `[pattern]` for the shipping abandonment (N=3 in same segment).
- `[anecdote]` for the QuickBooks request (N=1).
- P04 has no actionable insight; nothing written for them. (Critical: don't
  fabricate something just because a participant is on the list.)

**Step 3 — re-identification check.** Scans the proposed text. No real
names, no role+org+region tuples. The phrase "SMB founders" is a segment
descriptor, not a re-identification surface. Passes.

**Step 4a — write to `WORKSPACE_RESEARCH.md`.** Creates the file:

```markdown
# WORKSPACE RESEARCH
> Sidecar to WORKSPACE_BRAIN.md. Atomic user-research insights with
> pseudonymous provenance. NOT auto-injected — Claude reads on demand.
> Pseudonym ledger: ./research/pseudonyms.local.md (gitignored).

## STUDIES
- **2026-05-22-checkout-interviews**: 5 SMB founders, 30min remote
  semi-structured interviews. Recruited via UserInterviews.com.
  Pseudonyms P01-P05.

## INSIGHTS

- [pattern] (P01, P03, P05) [2026-05-22-checkout-interviews] — SMB
  founders abandon at checkout step 3 when shipping cost first appears.
  → implication: move shipping estimator earlier, OR surface a
    free-shipping threshold before step 1.
- [anecdote] (P02) [2026-05-22-checkout-interviews] — Wanted to import
  existing customers from QuickBooks; couldn't find the option.
```

**Step 4b — gated brain edits.**

The `[pattern]` shipping insight contradicts the 2026-05-19 decision about
shipping placement *and* resolves the open question about SMB shipping
placement. Per the gating table:

- It is a **`[pattern]` that contradicts a prior decision** → prepend to
  `OPEN QUESTIONS` (NOT to `DECISIONS LOG`).
- It is a **`[pattern]` that resolves an OPEN QUESTION** → the existing
  open question moves to `DECISIONS LOG` with citation.
- The `#401 Checkout flow polish` thread is in-flight and relevant → add
  a one-time suffix.
- This is the first time research touches "checkout flow" → add one
  SYNAPSES entry.

The `[anecdote]` QuickBooks insight does **not** edit the brain (gating
rule: anecdotes are sidecar-only unless `--escalate` is passed).

Resulting brain diff:

```diff
 ## ACTIVE THREADS
 - (in-progress) #432 Stripe webhook signing — branch `feat/stripe-signing`, ~80%
-- (in-progress) #401 Checkout flow polish — sprint goal, lots of small fixes
+- (in-progress) #401 Checkout flow polish — sprint goal, lots of small fixes
+  (see WORKSPACE_RESEARCH.md 2026-05-22-checkout-interviews)

 ## DECISIONS LOG
+- **2026-05-23**: Confirmed: shipping placement is wrong for SMB segment.
+  Reason: WORKSPACE_RESEARCH.md 2026-05-22-checkout-interviews — 3 of 5
+  SMB founders abandoned at the step-3 shipping reveal.
 - **2026-05-19**: Show shipping cost on checkout step 3 (cart confirmation).
   Reason: avoids surprise charges; matches Shopify-style flow we benchmarked.

 ## SYNAPSES
+- **WORKSPACE_RESEARCH.md** <-> **checkout flow** — see for behavioral evidence

 ## OPEN QUESTIONS
+- Reconsidering 2026-05-19 shipping placement — 3 of 5 SMB founders
+  abandon at step-3 reveal (triggered by WORKSPACE_RESEARCH.md
+  2026-05-22-checkout-interviews).
-- Is the checkout flow's shipping placement the right one for SMB customers?
```

Notice the old 2026-05-19 decision is **not deleted** — it stays in the
log as a record of what was believed. The new evidence shows up as a
fresh DECISIONS LOG entry citing the research and a "Reconsidering"
OPEN QUESTION that forces a follow-up. Append-only.

**Step 5 — lint, report, stop on conflicts.** Linter runs before and after:

```
$ python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md
brain_lint v1.0
Score: 83/100  (before)
Score: 83/100  (after)
```

The lint score is unchanged — the edits added a thread suffix, one
DECISIONS LOG entry (with `Reason:`), one SYNAPSES entry, and rotated
one open question. None of those move any axis materially.

Behavior-vs-opinion ratio: 2 of 2 captured insights cite past behavior
(abandoned a checkout, couldn't find a feature). 100% behavioral — well
above the 70% threshold. No warning.

Final report:

```
Mode: describe
Wrote N=2 insights to WORKSPACE_RESEARCH.md ([anecdote]=1, [pattern]=1).
Behavior-vs-opinion ratio: 2/2 = 100%  (ok).
Brain cross-refs: 1 thread annotated, 1 question resolved + 1 question added, 1 synapse added.
Conflicts with prior decisions: WORKSPACE_RESEARCH 2026-05-22-checkout-interviews challenges DECISIONS 2026-05-19: shipping-placement assumption.
Lint score (brain): 83/100 → 83/100.
Sidecar size: 0.6 KB.
Pseudonym ledger: present at ./research/pseudonyms.local.md (empty stub — populate from Notion).
```

Because the conflicts list is non-empty, Claude stops and surfaces it
to the user:

> ⚠️ This research session **challenges a prior decision** (2026-05-19
> shipping placement). The decision is still in the log; a reconsidering
> entry has been added to OPEN QUESTIONS. Recommend discussing before
> the next sprint planning, especially since #401 Checkout flow polish
> is currently in-flight.

## What did *not* happen (and why)

- **The 2026-05-19 decision was not deleted.** Decisions log is
  append-only. Future-you needs to see "we believed X, then we learned
  Y" — not "we always knew Y."
- **The QuickBooks anecdote did not edit the brain.** N=1, no escalation.
  It lives in the sidecar and will get cross-referenced if/when another
  participant raises the same point.
- **P04 produced no insight.** Don't manufacture one to make the
  participant count match. Silent participants are real.
- **No verbatim quotes in either file.** The "I closed the tab when I
  saw the cost" quote is paraphrased in the insight. If you want to
  preserve the verbatim, it goes in `./research/quotes.local.md`
  (gitignored) with an inline pointer in the insight:
  `(quote: quotes.local.md#L42)`.

## Follow-up: a week later

A second study (`2026-05-29-shipping-survey`, N=50) confirms the
shipping pattern. The right move is to **append a new dated line** in
WORKSPACE_RESEARCH.md citing the prior — not edit the original:

```markdown
- [pattern] (P01-P29 of 50) [2026-05-29-shipping-survey] — Survey
  replicates 2026-05-22 finding: 58% of SMB respondents cite shipping
  cost timing as their primary abandonment reason. Upgrades
  2026-05-22-checkout-interviews from interview-only to mixed-methods.
```

The original `[pattern]` stays untouched. History matters.
