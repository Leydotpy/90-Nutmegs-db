# SUBAGENT_ORCHESTRATOR.md — SANFootball Controlled Codex Execution

## 1. Authority

`AGENTS.md` is the single authoritative architecture and product specification. Concern files are scoped execution instructions derived from it. If a concern file appears to conflict with `AGENTS.md`, **stop and follow `AGENTS.md`**, record the conflict in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`, and do not invent a resolution that weakens security, data integrity, privacy, production infrastructure, or canonical ownership.

## 2. One-concern rule

Codex MUST work on **one concern ID at a time** unless the user explicitly authorizes a named set of concerns. Even when several concerns are technically parallelizable, do not batch them merely for convenience.

A concern may start only when every listed dependency is `APPROVED` in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`. `READY_FOR_REVIEW` is not sufficient.

## 3. Human approval rule

Codex may set a concern to:

- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_REVIEW`
- `DEFERRED` only when the user explicitly defers it or the master spec allows a documented deferral

Codex MUST NOT set its own concern to `APPROVED`. Approval is a human/reviewer action.

When implementation and tests for the current concern are complete, Codex MUST:

1. update the status document to `READY_FOR_REVIEW`;
2. provide the exact completion report required by the concern file;
3. list migrations, compatibility impact, tests, documentation, deleted legacy code, risks, and unresolved items;
4. STOP. Do not begin the next concern.

## 4. First actions for every concern

Before editing code, the active concern agent MUST:

1. read root `AGENTS.md` fully;
2. read this orchestrator;
3. read `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
4. read its own concern file;
5. inspect git status, branch, modified/untracked files and preserve user changes;
6. inspect relevant architecture docs/tests/models/migrations/routes/tasks/events/providers;
7. verify its dependency concerns are `APPROVED`;
8. verify the repository state still matches assumptions in the concern file;
9. update its board row to `IN_PROGRESS` and record start notes;
10. only then implement.

## 5. Required implementation loop

For each concern:

```text
inspect → characterize → design → implement → migrate → test → document → observe → remove superseded code → report → STOP FOR APPROVAL
```

Use expand → backfill → switch → verify → contract for high-value data migrations. Keep old/new application versions compatible across deployment windows where applicable.

## 6. Scope discipline

The active concern owns only its listed scope. If adjacent work is discovered:

- if required for correctness/security of the current concern, make the minimum dependency-safe change and record it;
- if it belongs to a later concern, record it under `Next Actions`/that concern's notes and do not implement it early;
- if it reveals a broken assumption in an already `APPROVED` concern, set the active concern to `BLOCKED`, document the regression/assumption, and ask for review rather than silently rewriting prior architecture.

## 7. No-redo rule

If a requested item is already correctly implemented and verified by code/tests/data constraints, do not rewrite it for style. Mark it `VERIFIED EXISTING` in the status document and continue with the missing pieces of the same concern.

## 8. Required quality checks

Every concern must apply relevant checks from the master specification, including:

- canonical ownership and no duplicate mutable state;
- server-side authorization;
- DB constraints/indexes/transactions;
- idempotency/retry safety;
- bounded queries/no N+1;
- background execution for heavy work;
- provider adapters and no provider IDs as canonical IDs;
- production statelessness/no durable local media;
- secure secret handling and log redaction;
- observability/failure state;
- migration/backfill/compatibility tests;
- documentation and status updates;
- removal of superseded code after migration verification.

## 9. Completion report contract

Every `READY_FOR_REVIEW` response must contain:

```text
Concern: SF-XX — <name>
Status: READY_FOR_REVIEW

Implemented:
- ...

Changed files:
- ...

Migrations/backfills:
- ...

Compatibility impact:
- ...

Tests/checks run:
- <command> — PASS/FAIL

Observability/operations impact:
- ...

Legacy code removed:
- ...

Known risks/deferred items:
- ...

Reviewer verification steps:
1. ...
2. ...

Recommended next concern after approval:
- SF-YY — ...
```

Do not claim tests passed if they were not run. Do not hide failures behind TODO comments.

## 10. Status semantics

Allowed values: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

- `NOT_STARTED`: dependency/order not yet satisfied or work not selected.
- `READY`: all dependencies approved and safe to begin.
- `IN_PROGRESS`: active Codex scope.
- `BLOCKED`: cannot safely proceed; reason/owner/exit condition required.
- `READY_FOR_REVIEW`: implementation finished; Codex must stop.
- `APPROVED`: human-reviewed checkpoint; dependents may begin.
- `DEFERRED`: explicitly postponed with rationale/risk/dependency.
- `SUPERSEDED`: concern is no longer independently required because a reviewed architecture change subsumed it; rationale required.

## 11. Parallel work

Parallel work is opt-in, not default. If the user later permits parallel Codex agents, only concerns with no dependency edge between them may run concurrently, each in an isolated branch/worktree with a merge-order plan recorded first.
