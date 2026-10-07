# SF-13 — Media Asset Model & Cloudflare Provider Boundary

**Status owner:** `SANFOOTBALL_IMPLEMENTATION_STATUS.md`  
**Execution mode:** one concern, human approval required before dependents  
**Derived from:** `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` (authoritative master architecture/product specification)

## Objective

Establish provider-neutral media ownership with Cloudflare-backed production adapters through pycflare only.

## Dependencies

- `SF-03` must be `APPROVED`.
- `SF-06` must be `APPROVED`.
- `SF-08` must be `APPROVED`.

## Master-spec source map

- `Part I §10`
- `Part I §50 Phase 9`
- `Part II §§13, 60, 75`
- `Part II §59.1`

## Mandatory operating rules

- Root `AGENTS.md` governs execution; `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` governs architecture/product requirements. Read only the master sections listed in this concern's source map by default, plus additional sections only when a material dependency, conflict, security issue, migration issue, or architecture ambiguity requires them.
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

- Canonical media asset/variant/provider-location model
- Audio role/format/codec/bitrate separation
- R2/Images/Stream provider adapters
- pycflare Git dependency pinned/locked to immutable revision
- Provider IDs isolated from domain identifiers
- Source/derivative lineage and processing state
- No durable production dependency on local media files

## Explicit non-goals / boundaries

- No direct boto3/raw Cloudflare REST parallel path where pycflare covers capability
- No provider ID as canonical episode/show ID

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

- [ ] Provider-neutral domain boundary exists
- [ ] pycflare is the normal Python Cloudflare path
- [ ] R2/Images/Stream responsibility is explicit
- [ ] Media lineage and status are testable

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
- next concern(s) unlocked **only after approval**: `SF-14, SF-15, SF-20`.

## Stop condition

Once this concern is `READY_FOR_REVIEW`, STOP. Do not edit or start any dependent concern until a human reviewer marks this concern `APPROVED` in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`.
