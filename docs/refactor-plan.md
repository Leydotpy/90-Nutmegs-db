# SF-00 repository characterization design

This is a design note for the baseline at `e24ff2e9c9ae7ecb563215f1cfc4f1b6e6687c6e`, not another implementation tracker. Concern state, findings and approval live only in [the execution ledger](../SANFOOTBALL_IMPLEMENTATION_STATUS.md).

## Scope and approach

SF-00 records the running Django application's shape and its existing safety checks. Preserve application code, settings, migrations, dependencies and public contracts. Produce current-state architecture and an evidence inventory, run the existing CI checks using Python 3.14 and isolated test settings, and distinguish pre-existing failures from changes introduced here. Use synthetic production settings for import/deploy checks; never contact production databases, providers or queues.

The repository already contains partial canonicalization. Classify each existing owner as canonical candidate, transitional, legacy or missing; a passing targeted test verifies only the behavior it exercises. No SF-00 finding establishes approval of another concern. No new domain owner, ADR, feature, constraint, migration, characterization test or deployment is introduced in this concern.

## Decisions

- Keep the modular monolith and its currently routed API intact. Map custom routing and loader callers before the future SF-04 removal.
- Treat existing access, podcast and media services as owners to verify and extend in their assigned concerns. Record duplicate state and compatibility projections explicitly.
- Inspect installed model metadata, URL resolution, migration definitions, task registrations and receiver imports. Runtime inventories use `conf.settings.test`; production topology is inferred from source only and remains unverified where no deployment evidence exists.
- Install locked web/dev dependencies for checks; leave optional media/ML worker extras uninstalled. Do not replace the Python 3.14 baseline with the host's Python 3.12, which cannot parse all source syntax.
- Record every applicable baseline check, including failures. A documentation baseline can be ready for review with known pre-existing defects; it does not certify production readiness.

## Approval boundary and subsequent work

The next recommended concern is SF-01 (Characterization Test Safety Net). SF-02 (Settings, Secrets & Environment Configuration) also becomes eligible only after a human approves SF-00. Both remain unstarted here. SF-01 should reuse existing tests, fill behavior gaps and make baseline failures reproducible; SF-02 should verify existing settings rather than replacing them by assumption.

Later code, schema, security, API, provider and operational changes follow the existing concern dependency graph in [DEPENDENCY_MAP.md](DEPENDENCY_MAP.md). Data changes must follow expand → backfill → switch → verify → contract with caller and rollback evidence. Concrete findings and exit conditions are recorded in the ledger rather than implemented ahead of their concern.

## Rollback and validation

SF-00 changes documentation only. Rollback is removal/reversion of those documentation changes; there is no data rollback or client transition. Existing migration and behavior tests run only on disposable test databases. Full production provider, PostgreSQL concurrency, worker, performance and restore exercises require later concern environments; report these limits explicitly.
