---
description: Capture and consult atomic user-research insights — provenance-checked, pseudonymous, with [pattern]-gated cross-references into the workspace brain
---

User-research findings are the gold-standard "non-derivable" knowledge: you
cannot infer "users abandon at checkout step 3" from `git log`, the schema,
or `CLAUDE.md`. The brain preserves *what we decided* and *why*; this
command preserves *what we heard from users* — the upstream evidence that
should be informing those decisions.

**The discipline test** — before writing any insight, ask: *would `git log`,
the schema, or `CLAUDE.md` already tell me this?* If yes, drop it. Skipping
the obvious is what makes the research log valuable.

### Architecture

| File | Purpose | Auto-injected? |
|------|---------|----------------|
| `WORKSPACE_BRAIN.md` | Decisions + threads + open questions | yes |
| `WORKSPACE_RESEARCH.md` (sidecar) | Atomic research insights with pseudonyms | no — read on demand |
| `./research/pseudonyms.local.md` | P01→real-person mapping | **never** — gitignored |
| `./research/quotes.local.md` | Verbatim quotes (if any) | **never** — gitignored |

Why a sidecar: bulk insights would blow the brain's `Section balance` axis
(40% max per section). The brain stays small; the log stays comprehensive;
high-signal `[pattern]` insights surface as **annotations** on existing
brain entries — not as bulk text. Mirrors the `WORKSPACE_BRAIN_ARCHIVE.md`
pattern.

Discoverability: the `SessionStart` hook injects a breadcrumb noting
`WORKSPACE_RESEARCH.md` exists, so future-Claude knows to consult it.

### Hard rule: never fabricate

Refuse to invent participants, dates, methods, quotes, or counts. If
provenance is missing, write `(source: ?)` and stop. This log will be
cited as primary evidence in future decisions — its trustworthiness is
the whole point.

---

### Modes (pick one based on user args / prompt)

| Mode | When to use | Writes? |
|------|-------------|---------|
| `describe` | User narrates a session they just ran | yes |
| `from-notes` | User pastes already-paraphrased notes (one paragraph per finding) | yes |
| `synthesize` | User asks to consolidate existing sidecar entries into a higher-confidence pattern | yes (sidecar only) |
| `consult <question>` | User asks "what did we hear about X?" — read-only query | **no** |

If the user wants to paste raw transcripts >2 KB, **stop and ask them to
paraphrase first**. That curation is the value-add and is not what this
command does (cf. `CONTRIBUTING.md`: "no auto-extraction from
transcripts").

---

### Step 1 — provenance gate (write modes only)

Use `AskUserQuestion` if available. All four required:

1. **Study slug**, e.g. `2026-05-22-checkout-interviews`.
2. **Method**: `interviews` / `survey` / `support-tickets` /
   `sales-calls` / `in-app feedback` / `observation` / other.
3. **N + segment**, e.g. `5 SMB founders, recruited via UserInterviews`.
4. **Pseudonym ledger**: run this first —
   ```bash
   test -f ./research/pseudonyms.local.md && echo "found" || echo "missing"
   ```
   - **found** → great, proceed.
   - **missing** → ask: "create stub now, supply mapping inline, or
     proceed `[anecdote]`-only with `(no ledger)` ad-hoc IDs?"
     If the user picks "create stub", `mkdir -p ./research && touch
     ./research/pseudonyms.local.md` and remind them to add
     `research/*.local.md` to `.gitignore`. Refuse to invent ledger
     entries on the user's behalf.

Side-conditions (apply during Step 2):

- Study **>6 months old** → tag every insight `[anecdote]` regardless
  of N. User populations drift.
- Input mostly **hypothetical opinions** ("would you use…") → surface:
  > "Thin behavioral signal. Capturing N=<low>; recommend re-running
  > with past-behavior questions (cf. *The Mom Test*)."
  Then proceed only with the behavioral subset.

### Step 2 — extract atomic insights

One claim per line. Format:

```
- [pattern] (P03, P05) [2026-05-22-checkout-interviews] — Users abandon
  checkout when shipping cost first appears at step 3.
  → implication: move shipping estimator earlier, OR surface a
    free-shipping threshold before step 1.
```

Schema rules:

| Rule | Why |
|------|-----|
| Confidence: `[anecdote]` (N=1) or `[pattern]` (N≥2 in same segment) | Qual N alone never reaches "strong" — that's misleading |
| Sources in parens, pseudonyms only: `(P03, P05)` | Distinct from `[confidence]` tag visually |
| One claim per line | Combining collapses provenance |
| Paraphrase, never verbatim quote | Reduces re-identification surface |
| Optional `→ implication` is a hypothesis, **never** a decision | Decisions belong in `DECISIONS LOG` |
| Verbatim quotes → `./research/quotes.local.md` with an inline reference: `(quote: quotes.local.md#L42)` | Keeps PII out of the shareable log |

**Iteration**: to upgrade `[anecdote]` → `[pattern]` after a new
confirming source, **append** a new dated line citing the prior. Never
edit history in place.

### Step 3 — re-identification check (privacy gate)

Before any edit, scan the proposed text for **re-identification tuples**:
any combination of (role, organization, region, time-window) that could
pin down a single person even without a name. Examples to reject:

- ❌ "the CTO of a Series A fintech in Toronto, May 2026"
- ❌ "P03 (a hospital network IT director in the EU)"
- ❌ "our biggest enterprise customer's payments lead"

Also flag real names, emails, employers, phone numbers, addresses. If you
can't strip the identifying tuple without losing the insight, **paraphrase
to a generic claim** ("payments leads at enterprise customers report…")
rather than anonymize. **Confirm with the user before writing** if any
such content is present. Assume `WORKSPACE_RESEARCH.md` is team-public
once committed.

### Step 4 — write sidecar, then [pattern]-gate the brain

**Part A — write to `WORKSPACE_RESEARCH.md`** (Edit, or Write if absent;
template below). Prepend new insights at the top.

```markdown
# WORKSPACE RESEARCH
> Sidecar to WORKSPACE_BRAIN.md. Atomic user-research insights with
> pseudonymous provenance. NOT auto-injected — Claude reads on demand.
> Pseudonym ledger: ./research/pseudonyms.local.md (gitignored).

## STUDIES
- **<study-slug>**: <N + segment>, <method>. Pseudonyms <P01-Pxx>.

## INSIGHTS
*([anecdote]=N=1 · [pattern]=N≥2 in same segment. Pseudonyms only.)*

- [pattern] (P03, P05) [<study-slug>] — <claim>.
  → implication: <one-line hypothesis>.
```

**Part B — cross-reference the brain** (the gating rules, in one table).
Rows are **cumulative**: apply every matching row up to its cap. If one
`[pattern]` insight both supports a thread *and* resolves a question,
both edits get made.

| Insight type | Allowed brain edits | Cap per run |
|--------------|---------------------|-------------|
| `[anecdote]` | none — sidecar only | 0 |
| `[anecdote]` + user passed `--escalate "<reason>"` | one OPEN QUESTIONS entry tagged `(escalated anecdote)` | 1 |
| `[pattern]` supports an in-flight thread | suffix on thread line: `(see WORKSPACE_RESEARCH.md <study-slug>)` | 1 per thread |
| `[pattern]` resolves an OPEN QUESTION | move to `DECISIONS LOG` with `Reason: <study-slug>` | unlimited |
| `[pattern]` raises a new question | prepend to OPEN QUESTIONS: `<question> (triggered by WORKSPACE_RESEARCH.md <study-slug>)` | **≤2 per run** — surplus stay in sidecar |
| `[pattern]` contradicts a prior decision | prepend to OPEN QUESTIONS: `Reconsidering <decision date> — <one-line conflict> (triggered by WORKSPACE_RESEARCH.md <study-slug>)` | **≤2 per run** — surplus stay in sidecar |
| First time research touches any topic in the brain | one SYNAPSES entry: `**WORKSPACE_RESEARCH.md** <-> **<topic>** — see for behavioral evidence` | 1 ever per topic |

Never edit prior decisions in `DECISIONS LOG`. The log is append-only;
challenges go through `OPEN QUESTIONS` first.

### Step 5 — lint, report, stop on conflicts

Run the linter explicitly so the report numbers are real:

```bash
python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md
```

Run it before Step 4 edits *and* after, so the delta is honest.

Also compute a **behavior-vs-opinion ratio** on the captured insights —
of the N captured, how many cite past behavior (what they *did*) vs.
hypothetical opinion (what they'd *do*)? If <70%, warn the user that
the input was opinion-heavy and offer to re-run with Mom-Test-style
prompts on the next study.

End with exactly this template:

```
Mode: <describe|from-notes|synthesize|consult>
Wrote N=<X> insights to WORKSPACE_RESEARCH.md ([anecdote]=<a>, [pattern]=<p>).
Behavior-vs-opinion ratio: <a/X>  (<warn / ok>).
Brain cross-refs: <T> threads annotated, <Q> questions added/resolved, <S> synapses added.
Conflicts with prior decisions: <"WORKSPACE_RESEARCH <slug> challenges DECISIONS <date>: <reason>" per line; "none" if none>.
Lint score (brain): <before>/100 → <after>/100.
Sidecar size: <K.K> KB.
Pseudonym ledger: <present | NOT FOUND — please create at ./research/pseudonyms.local.md>.
```

**If the conflicts list is non-empty, stop and surface it** before
moving on. A research session that challenges a recent decision is the
single most important signal this command produces — don't bury it.

### Consult mode (read-only)

When the user invokes `consult <question>` (or `/user-research consult …`):

1. **Read** `WORKSPACE_RESEARCH.md`. If it doesn't exist: "No
   `WORKSPACE_RESEARCH.md` yet. Use `describe` or `from-notes` mode to
   create one." Stop.
2. Match insights by **case-insensitive substring** on the user's
   question terms, OR by **SYNAPSES topic match** (any
   `WORKSPACE_RESEARCH.md <-> <topic>` synapse in the brain whose topic
   appears in the user's question). Don't synthesize — quote the
   matching insights verbatim with their provenance.
3. Group by confidence ([pattern] first, then [anecdote]), newest in
   each group first.
4. If zero matches: "No insights about `<topic>` in
   `WORKSPACE_RESEARCH.md`. The brain has <list> related decisions /
   threads / questions." Don't fabricate.
5. End with: `Consulted N=<X> insights ([pattern]=<p>, [anecdote]=<a>)
   across <S> studies. No brain edits made.`

---

### Notes

- See `examples/user-research-walkthrough.md` for a fully worked example
  (a 5-interview checkout study from describe → sidecar → brain edits →
  report).
- **Scope**: qualitative only. Pure quant (funnel data, A/B results)
  belongs in the brain's `KEY NUMBERS` section.
- **Archive cadence**: when `WORKSPACE_RESEARCH.md` exceeds ~50 KB or
  one year, rotate oldest STUDIES + INSIGHTS into
  `WORKSPACE_RESEARCH_ARCHIVE.md` (same pattern as `/brain-archive`).
- **Env vars**: `RESEARCH_FILE` overrides the sidecar path; honored by
  both this command and `brain_session_start.py` (which emits the
  discoverability breadcrumb).
- **What to capture / skip** (cf. *The Mom Test*):
  - ✔ Past behavior, specific incidents, workarounds, negative
    findings, surprising quotes.
  - ✘ Hypothetical opinions, generic feature requests, demographic-only
    data, compliments without substance.
