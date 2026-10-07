# CODEX_START_PROMPTS.md

## Start one concern

```text
Read AGENTS.md, SUBAGENT_ORCHESTRATOR.md, SANFOOTBALL_IMPLEMENTATION_STATUS.md, and agents/<CONCERN_FILE>.md in full.
Implement ONLY that concern. Verify all dependencies are APPROVED first. Preserve my existing changes. Update the status row to IN_PROGRESS before work. When the concern is complete, run all applicable tests/checks, update documentation/status, set it to READY_FOR_REVIEW, give me the required completion report, and STOP. Do not start any later concern until I approve this one.
```

## Resume a concern after review comments

```text
Resume only <SF-XX>. Read my review comments and the current repository/status first. Keep the concern IN_PROGRESS while fixing the issues. Re-run the relevant tests/checks. Return it to READY_FOR_REVIEW and STOP again.
```

## Approve and prepare the next concern

```text
I have reviewed <SF-XX> and approve it. Mark <SF-XX> APPROVED in SANFOOTBALL_IMPLEMENTATION_STATUS.md with the review note. Recompute which concerns are READY from the dependency graph, but do not implement the next concern until I explicitly name it.
```

## Reject / send back

```text
I do not approve <SF-XX>. Change it from READY_FOR_REVIEW to IN_PROGRESS and address only these review findings: <findings>. Do not advance any dependent concern.
```

## Inspect without implementing

```text
Audit <SF-XX> against AGENTS.md and its concern file. Do not modify code. Tell me what is already compliant, what is missing, what would change, what migrations/risks are involved, and whether its dependencies are genuinely satisfied.
```
