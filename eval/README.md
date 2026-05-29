# Brain quality eval

Two flavors of evaluation are baked in: a **static linter** (no LLM, deterministic)
and an **AI-graded review** (Claude reads the brain and scores it).

## Static linter

Lives at `template/.claude/scripts/brain_lint.py`. After install, runs in-project:

```bash
python .claude/scripts/brain_lint.py [path-to-brain.md]
```

Scores 6 axes (total 100). See the [main README](../README.md#the-linter) for details.

The linter is intentionally simple: no AST, no LLM call, no dependencies beyond
the stdlib. It catches the cheap stuff (file too big, no Reason: rationale,
stale Last sync date) so you save the LLM round-trip for the harder questions.

## AI-graded review

The `/brain-grade` slash command (defined in `template/.claude/commands/brain-grade.md`)
asks Claude to:

1. Run the static linter and report its findings.
2. Read the brain and score it 0-10 on **freshness**, **signal-to-noise**,
   **specificity**, **reason coverage**, and **section balance**.
3. Propose 1-3 specific edits (entries to remove, rewrite, archive) with
   exact Edit-tool calls — wait for your approval before applying.
4. Emit a final line: `Brain quality: <score>/100. <one-sentence recommendation>.`

Run after big sessions or every couple of weeks.

## Building your own brain eval

If you want to compare brain-on vs brain-off objectively, the recipe is:

1. Snapshot the brain (`cp WORKSPACE_BRAIN.md WORKSPACE_BRAIN.bak`).
2. Start a fresh session, ask Claude a project-specific question that depends
   on brain content (e.g., "what's the current deploy state? which threads are
   blocked? what was the most recent decision?").
3. Score the answer 0-3 on accuracy.
4. Disable the SessionStart hook (`mv .claude/hooks/brain_session_start.py /tmp/`).
5. Start another fresh session, ask the same question.
6. Score again. The delta is your brain's value.

That's the manual version. For the automated equivalent, the repo ships
**`eval/abtest.py`** (described next).

## Automated A/B harness (`eval/abtest.py`)

The harness runs the loop above for you, over a held-out question set, with a
judge model scoring both answers blind:

```bash
export ANTHROPIC_API_KEY=sk-...
pip install anthropic
python -m eval.abtest --runs 3        # or: python brain.py eval --runs 3
python -m eval.abtest --dry-run       # print the prompts, make no API calls
```

It asks each brain-dependent question in `eval/questions.json` twice — with and
without the brain in the system prompt — then a judge scores both 0-30 on
accuracy / specificity / usefulness and reports the mean delta + 95% CI. Defaults
to Haiku for the answers and Sonnet for the judge; override with
`ABTEST_ANSWER_MODEL` / `ABTEST_JUDGE_MODEL`. Point it at your real brain with
`--brain ./WORKSPACE_BRAIN.md`. See the
[main README](../README.md#the-eval-harness--does-the-brain-actually-help) for
example output and cost.
