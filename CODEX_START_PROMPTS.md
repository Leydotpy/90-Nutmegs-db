# CODEX_START_PROMPTS.md

## Recommended first prompt — start SF-00

```text
We are beginning the controlled SANFootball implementation programme.

Work on SF-00 only: Baseline & Repository Characterization.

Follow the root AGENTS.md execution protocol.

Read:
- AGENTS.md
- SUBAGENT_ORCHESTRATOR.md
- SANFOOTBALL_IMPLEMENTATION_STATUS.md
- agents/SF-00_baseline_repository_characterization.md
- docs/SOURCE_SECTION_MAP.md
- only the sections of docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md referenced by SF-00, plus any additional master section that a concrete dependency, conflict, security, migration, or architecture issue genuinely requires.

Do not load or implement the complete master specification wholesale.

Before making code changes:
1. inspect the repository and current git state;
2. preserve all existing user changes;
3. verify SF-00 has no unsatisfied dependencies;
4. mark SF-00 IN_PROGRESS in SANFOOTBALL_IMPLEMENTATION_STATUS.md.

Then perform only SF-00.

Do not implement SF-01, SF-02, or any later concern even if you discover work belonging to them. Record such findings in the status document instead.

When SF-00 is complete:
- run every applicable validation/check required by SF-00;
- update SANFOOTBALL_IMPLEMENTATION_STATUS.md;
- mark SF-00 READY_FOR_REVIEW;
- provide the required completion report and reviewer verification steps;
- STOP.

You are not authorised to mark SF-00 APPROVED.
I will review and approve it manually before another concern begins.
```

## Start any later concern

```text
Proceed with <SF-XX> only.

Follow AGENTS.md and SUBAGENT_ORCHESTRATOR.md.
Read SANFOOTBALL_IMPLEMENTATION_STATUS.md, the active agents/<SF-XX_...>.md file, docs/SOURCE_SECTION_MAP.md, and only the preserved master-specification sections referenced by that concern. Read additional master sections only when materially necessary.

Verify every dependency is APPROVED. Preserve my existing changes. Set only <SF-XX> to IN_PROGRESS before implementation.

Implement only <SF-XX>. Record later-scope discoveries instead of implementing them early.

When finished, run the required checks, update documentation/status, mark <SF-XX> READY_FOR_REVIEW, give me the required completion report and STOP. Do not begin another concern.
```

## Resume a concern after review comments

```text
Resume only <SF-XX>. Read my review comments and the current repository/status first. Re-read only the active concern and master sections needed for those review findings. Keep the concern IN_PROGRESS while fixing the issues. Re-run the relevant tests/checks. Return it to READY_FOR_REVIEW and STOP again.
```

## Approve and prepare the next concern

```text
I have reviewed <SF-XX> and approve it. Mark <SF-XX> APPROVED in SANFOOTBALL_IMPLEMENTATION_STATUS.md with the review note. Recompute which concerns are READY from the dependency graph, but do not implement any of them until I explicitly name one.
```

## Reject / send back

```text
I do not approve <SF-XX>. Change it from READY_FOR_REVIEW to IN_PROGRESS and address only these review findings: <findings>. Do not advance any dependent concern.
```

## Inspect without implementing

```text
Audit <SF-XX> against its concern file, the current approved implementation status, and only the relevant sections of docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md. Do not modify code. Tell me what is already compliant, what is missing, what would change, what migrations/risks are involved, and whether its dependencies are genuinely satisfied.
```
