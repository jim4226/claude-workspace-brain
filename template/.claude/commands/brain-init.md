---
description: Interactively scaffold a personalized WORKSPACE_BRAIN.md from a fresh template
---

Bootstrap a workspace brain for this project. Goal: take the user from "empty
template" to "useful brain" in under 60 seconds.

### Step 1 — check current state

Read `WORKSPACE_BRAIN.md` at the project root.

- If it doesn't exist, copy the template at `.claude/scripts/../WORKSPACE_BRAIN.md`
  (or fetch from https://raw.githubusercontent.com/jim4226/claude-workspace-brain/main/template/WORKSPACE_BRAIN.md
  if not present) to the project root.
- If it exists AND has already been customised (any section has non-template
  content), **stop** and report back: "Brain already initialised. Use `/brain`
  to edit a section, or `/brain-grade` to audit quality." Do not proceed.
- If it exists but is still the unedited template, proceed.

### Step 2 — ask the user 6 fast questions

Use AskUserQuestion (if available) or plain prompts. Keep each question to one
line. Wait for the user's answer before asking the next.

1. **Project type?** (web app | research / paper | ML training | CLI tool | other)
2. **One-line goal**: what are we building, in one sentence?
3. **Current sprint focus**: what are you trying to ship this week / cycle?
4. **One in-flight thread**: name one piece of work that's currently happening,
   with status (in-progress / blocked / pending).
5. **One recent decision** + the *why*: what's a judgment call you made in the
   last week and why? (Required - decisions without rationale rot fast.)
6. **One open question**: what's still unresolved?

### Step 3 — fill the template

Use the **Edit** tool to populate the brain:

- `ACTIVE FOCUS` → answer 2 + answer 3
- `ACTIVE THREADS` → one entry from answer 4
- `DECISIONS LOG` → one entry from answer 5, formatted
  `- **YYYY-MM-DD**: <decision>. Reason: <why>.` (use today's date)
- `OPEN QUESTIONS` → one entry from answer 6
- Set `Last sync:` in the header to today's date
- Leave `SYNAPSES`, `KEY NUMBERS`, `RECENT SESSIONS` with their template
  placeholders for now - the user can fill them as they accumulate.

For project-type-specific tweaks based on answer 1, see the examples in
the `examples/` directory of the repo (research-project.md, web-app.md).

### Step 4 — verify and report

Run `python .claude/scripts/brain_lint.py WORKSPACE_BRAIN.md` and report the
score. A well-initialised brain should score >=70/100.

End with:

> Brain initialised at WORKSPACE_BRAIN.md. Score: <N>/100.
> Hooks are wired; next session will start with this brain auto-injected.
> Run `/brain-grade` after a week to audit quality, or `/brain-archive` when
> active threads accumulate too many completed items.
