# Security Policy

## Supported versions

Latest minor version on `main` only. This project doesn't backport.

## Reporting a vulnerability

Email **jim4226@miami.edu** with `[security]` in the subject. Expect a
response within 72 hours.

Please do not file a public issue for security problems.

## Threat model — what's in scope

The hooks execute Python in the user's shell with the user's permissions.
That's by design (it's how Claude Code hooks work). In-scope issues:

- A crafted `WORKSPACE_BRAIN.md` causing the hooks or linter to execute
  arbitrary code (we treat the brain as untrusted input).
- A crafted brain file causing the HTML viewer to escape its sandbox
  (cross-site scripting via injected markdown).
- The installer overwriting or corrupting files outside the target
  directory.
- A crafted `settings.json` in the target directory causing the installer
  to escalate privileges or write outside the project.

## Out of scope

- A user manually pasting secrets into their brain file and committing
  them. Don't do that — review your commits.
- A user installing the package from a fork or mirror that has been
  tampered with. Verify the canonical source:
  `https://github.com/jim4226/claude-workspace-brain`.
- Vulnerabilities in third-party tools (Claude Code, the Anthropic SDK,
  Python). Report those to their respective projects.

## Known risk: hook output is trusted by Claude

The `SessionStart` and `PreCompact` hooks emit text that Claude treats as
system context. If your brain contains adversarial instructions, Claude
will read them. Treat the brain like any other file in your repo —
review changes before committing.
