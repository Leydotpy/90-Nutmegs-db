# SF-20 — Core Refactor Hardening Gate

**Status owner:** `SANFOOTBALL_IMPLEMENTATION_STATUS.md`  
**Execution mode:** one concern, human approval required before dependents  
**Derived from:** authoritative root `AGENTS.md`

## Objective

Verify that the canonicalisation programme is actually complete enough to become the baseline for feature expansion.

## Dependencies

- `SF-02` must be `APPROVED`.
- `SF-03` must be `APPROVED`.
- `SF-04` must be `APPROVED`.
- `SF-05` must be `APPROVED`.
- `SF-06` must be `APPROVED`.
- `SF-07` must be `APPROVED`.
- `SF-08` must be `APPROVED`.
- `SF-09` must be `APPROVED`.
- `SF-10` must be `APPROVED`.
- `SF-11` must be `APPROVED`.
- `SF-12` must be `APPROVED`.
- `SF-13` must be `APPROVED`.
- `SF-14` must be `APPROVED`.
- `SF-15` must be `APPROVED`.
- `SF-16` must be `APPROVED`.
- `SF-17` must be `APPROVED`.
- `SF-18` must be `APPROVED`.
- `SF-19` must be `APPROVED`.

## Master-spec source map

- `Part I §§32–36, 42–44, 51, 54–55, 66`
- `Part I Phase 14`

## Mandatory operating rules

- Root `AGENTS.md` remains authoritative.
- Read `SUBAGENT_ORCHESTRATOR.md` and `SANFOOTBALL_IMPLEMENTATION_STATUS.md` before editing.
- Work on **this concern only**.
- Preserve user modifications and inspect git status/branch first.
- Do not redo already-correct work; verify it and record it.
- Extend canonical owners; never create a parallel mutable source of truth for convenience.
- Use safe, reviewable migrations and trace callers before deletion.
- Keep the repository runnable at review boundaries.
- Update the single status document continuously.
- When complete, set this concern to `READY_FOR_REVIEW` and **STOP**. Never self-mark `APPROVED`.

## Scope owned by this concern

- Query profiling and N+1 review
- Security/rate-limit/dependency audit
- Migration verification
- Compatibility/deprecation cleanup
- Backup/restore verification
- Observability and runbook baseline
- End-to-end acceptance scenarios
- Delete superseded code that is now safe to remove
- Architecture/data/commercial/security/performance/testing/docs review

## Explicit non-goals / boundaries

- No new product features

## Required inspection before implementation

1. Identify the current canonical owner(s) touched by this concern.
2. Trace public/internal callers, serializers/views, tasks, signals/events and admin/operator paths.
3. Inspect relevant models, constraints, indexes and migrations.
4. Inspect tests and add characterization coverage before replacing high-risk behavior.
5. Check security, authorization, retry/idempotency, query, cache and concurrency implications.
6. Check production hosting/storage/provider/queue/backup/observability/cost implications where relevant.
7. Record any already-correct implementation under `Verified Existing Implementations` rather than rewriting it.

## Implementation checklist

- [ ] Record concern as `IN_PROGRESS` with start notes/commit/branch.
- [ ] Produce a short repository-specific design note before invasive changes.
- [ ] Implement the smallest coherent increment that satisfies this concern.
- [ ] Use expand → backfill → switch → verify → contract for risky data changes.
- [ ] Add/adjust DB constraints and indexes where invariants/query paths require them.
- [ ] Migrate callers to canonical services/policies/selectors.
- [ ] Add retry/idempotency/failure-state handling where retries or external providers are involved.
- [ ] Add bounded queries and prevent N+1 behavior on high-traffic paths.
- [ ] Add observability for important failures/transitions.
- [ ] Update API/schema/docs/ADR/runbooks where the contract changes.
- [ ] Delete superseded code only after data/caller/compatibility verification.
- [ ] Run relevant unit, integration, migration, security, performance and end-to-end checks.
- [ ] Update all relevant sections of the single status document.
- [ ] Set this concern to `READY_FOR_REVIEW` and stop.

## Concern-specific acceptance gate

- [ ] All relevant Part I phase gates pass
- [ ] No protected-media authorization bypass remains
- [ ] No unresolved duplicate mutable source of truth in dependent domains
- [ ] Repository is runnable and documented
- [ ] Status board can declare core refactor APPROVED

## Required review packet

At `READY_FOR_REVIEW`, report:

- exact files changed;
- architectural decisions and canonical owner(s);
- migrations/backfills and rollback/compatibility notes;
- API/client behavior changes;
- tests/checks actually run with PASS/FAIL;
- query/performance/concurrency implications;
- security/privacy/entitlement implications;
- infrastructure/provider/queue/storage/backup/cost implications where applicable;
- legacy code removed;
- unresolved risks/deferred items;
- step-by-step reviewer verification;
- next concern(s) unlocked **only after approval**: `SF-21, SF-22, SF-23`.

## Stop condition

Once this concern is `READY_FOR_REVIEW`, STOP. Do not edit or start any dependent concern until a human reviewer marks this concern `APPROVED` in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`.
