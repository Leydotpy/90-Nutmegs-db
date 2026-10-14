# 90nutmgs backend (SANFootball)

This repository contains a Django/DRF modular monolith in `app/` and the controlled SANFootball implementation programme below. Python **3.14 or newer** is required; use the committed `uv.lock` for reproducible dependencies.

```bash
uv sync --locked --extra dev
uv run --locked python app/manage.py check --settings=conf.settings.test
uv run --locked python app/manage.py test --settings=conf.settings.test
```

The approved SF-00 [baseline validation](docs/baseline-validation.md) records the original failures and limitations. SF-01 fixes the stale liveness assertion and scoped test formatting, and adds characterization coverage; see [testing](docs/testing.md). SF-03 updates the audited dependencies and introduces separate web/worker process commands; see the runtime and dependency guides below. Current results and review state are in the [execution ledger](SANFOOTBALL_IMPLEMENTATION_STATUS.md).

For local development, review `.env.example`, select `conf.settings.development`, migrate a **local disposable database**, and run the development server:

```bash
uv run --locked python app/manage.py migrate --settings=conf.settings.development
uv run --locked python app/manage.py runserver --settings=conf.settings.development
```

Development defaults to SQLite/locmem. Test settings isolate external services. WSGI, ASGI and Celery default to production settings, which require PostgreSQL, Redis, identity and media configuration. Development startup does not establish that provider-backed operations work. Optional `media-workers` and `recommendation-workers` extras supply heavyweight dependencies; they are not installed by the commands above. Never enable the production R2 cutover confirmation merely to bypass startup validation.

Read [configuration and secret handling](docs/configuration.md) before selecting production settings, setting proxy trust/HSTS, or rotating credentials. Production requires explicit HTTPS public/Giffy endpoints; `.env.example` is a local template, not a deployment configuration.

- [Current architecture](docs/architecture-current.md) — current owners, compatibility paths, infrastructure and unknowns.
- [Evidence inventory](docs/baseline-inventory.md) — apps, models/relations, migrations, routes, tasks/signals, tests and dependencies.
- [SF-00 design note](docs/refactor-plan.md) — scope, decisions, rollback and approval boundary.
- [Runtime processes](docs/runtime.md) — web/worker/scheduler commands, queue rollout and shutdown budgets.
- [Identity and authorization](docs/identity-and-authorization.md) — canonical Clerk mapping, staff access, privacy and audit contracts.
- [API structure](docs/api-structure.md) — URL includes, feature ownership and compatibility verification.
- [Content canonicalization](docs/content-canonicalization.md) — ownership, taxonomy, sports metadata and migration compatibility.
- [Dependencies](docs/dependencies.md) — install profiles, supported runtime, audit results and upgrade procedure.
- [Execution ledger](SANFOOTBALL_IMPLEMENTATION_STATUS.md) — sole concern tracker and risk/action record.

## Controlled implementation programme

This package decomposes the SANFootball master implementation programme into **46 narrow, reviewable concern agents** with explicit dependencies and human approval gates.

## Important architecture change in this revised pack

The original 9,000+ line master specification is **no longer the root `AGENTS.md`**.

Instead:

- `AGENTS.md` is now a compact execution/orchestration instruction file intended to be loaded by Codex on every run.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` contains the **complete original master specification, preserved verbatim**, and remains the architecture/product authority.
- each `agents/SF-XX_*.md` file identifies the master sections relevant to that concern;
- Codex reads only those relevant master sections by default, not the entire master on every task.

This preserves the master specification without wasting context or encouraging Codex to implement unrelated work.

## Control model

1. Root `AGENTS.md` defines the execution protocol.
2. The preserved master specification defines the target architecture and product requirements.
3. `SUBAGENT_ORCHESTRATOR.md` defines the execution/approval protocol in detail.
4. `SANFOOTBALL_IMPLEMENTATION_STATUS.md` is the **single implementation-status document** required by the master specification.
5. Pick **one** concern whose dependencies are `APPROVED`.
6. Codex changes that concern to `IN_PROGRESS`, implements only that scope, then changes it to `READY_FOR_REVIEW`.
7. Codex **must stop** at `READY_FOR_REVIEW`. It may never self-promote to `APPROVED`.
8. After you inspect the work, approve it (or return it to `IN_PROGRESS`/`BLOCKED`).
9. Only then may a dependent concern start.

Allowed statuses: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

## Files

- `AGENTS.md` — compact Codex operating rules and selective-loading protocol.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` — untouched authoritative master architecture/product specification.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.sha256` — checksum of the preserved master.
- `SUBAGENT_ORCHESTRATOR.md` — coordination, stop conditions, approval protocol, and reporting contract.
- `SANFOOTBALL_IMPLEMENTATION_STATUS.md` — authoritative execution board and repository status ledger.
- `CODEX_START_PROMPTS.md` — reusable prompts, including the recommended first SF-00 prompt.
- `docs/DEPENDENCY_MAP.md` — dependency waves and graph-readable index.
- `docs/SOURCE_SECTION_MAP.md` — concern-to-master-spec mapping.
- `docs/CONCERN_MANIFEST.md` — all 46 concerns and their objectives.
- `agents/SF-XX_*.md` — concern-specific implementation agents.

## How to install into the SANFootball repository

Copy the **contents of this package directory** into the root of the SANFootball repository. Preserve your existing code and review conflicts before overwriting any repository documentation with the same names.

The expected repository-level control files should then include:

```text
AGENTS.md
SUBAGENT_ORCHESTRATOR.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
CODEX_START_PROMPTS.md
agents/
docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md
docs/DEPENDENCY_MAP.md
docs/SOURCE_SECTION_MAP.md
docs/CONCERN_MANIFEST.md
```

## Start here

Open `CODEX_START_PROMPTS.md` and use **Recommended first prompt — start SF-00**.

Do not ask Codex to “implement everything in the agents folder.” The entire structure is designed around one concern → review → approval → next concern.
