# SANFootball Implementation Status

> **Authoritative execution ledger.** This is the single repository-wide implementation-status document required by `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md`. Root `AGENTS.md` governs how Codex uses it. Do not create competing phase/status files.

## Current Master Phase

Master Phase 5 — SF-00 through SF-06 approved; SF-07, SF-10, SF-16 and SF-17 are newly READY.

## Current Subphase

SF-06 human approval recorded 2026-10-14. Publishing the approved SF-00–SF-06 checkpoint on `codex/approved-sf00-sf06`, then implementing the newly READY set sequentially on a separate local branch.

## Concern Execution Board

Allowed statuses: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

| ID | Concern | Dependencies | Status | Reviewer / Approval Ref | Notes / Blocker |
|---|---|---|---|---|---|
| SF-00 | Baseline & Repository Characterization | — | `APPROVED` | User approval in this chat, 2026-10-11 | Human reviewed and approved SF-00; recorded by Codex at user direction. Baseline findings retained. |
| SF-01 | Characterization Test Safety Net | SF-00 | `APPROVED` | User approval in this chat, 2026-10-11 | Human reviewed and approved this implementation; recorded by Codex at user direction. Review packet retained. |
| SF-02 | Settings, Secrets & Environment Configuration | SF-00 | `APPROVED` | User approval in this chat, 2026-10-11 | Human reviewed and approved this implementation; recorded by Codex at user direction. Review packet retained. |
| SF-03 | Dependency, Runtime & Process Isolation | SF-02 | `APPROVED` | User approval in this chat, 2026-10-13 | Human reviewed and approved; recorded by Codex at user direction. Validation caveats remain in review packet. |
| SF-04 | Legacy Framework & API Structure Removal | SF-01, SF-02 | `APPROVED` | User approval in this chat, 2026-10-13 | Human reviewed and approved; recorded by Codex at user direction. Validation caveats remain in review packet. |
| SF-05 | Identity, Authentication & Authorization Foundation | SF-01, SF-02 | `APPROVED` | User approval in this chat, 2026-10-13 | Human reviewed and approved; recorded by Codex at user direction. Validation caveats remain in review packet. |
| SF-06 | Podcast Content & Sports Metadata Canonicalization | SF-04 | `APPROVED` | User approval in this chat, 2026-10-14 | Human reviewed and approved SF-06; recorded by Codex at user direction. Review packet and rollout limits retained. |
| SF-07 | Plan, Price, Subscription & Entitlement Models | SF-05, SF-06 | `READY` | — | Dependencies approved; user authorizes implementation of all newly READY concerns. |
| SF-08 | Canonical Access Policy | SF-07 | `NOT_STARTED` | — | — |
| SF-09 | Billing Provider & Webhook Lifecycle | SF-08 | `NOT_STARTED` | — | — |
| SF-10 | Playback Progress & Continue Listening | SF-05, SF-06 | `READY` | — | Dependencies approved; user authorizes implementation of all newly READY concerns. |
| SF-11 | Queue / Up Next Rewrite | SF-10 | `NOT_STARTED` | — | — |
| SF-12 | Library: Follows, Playlists & Bookmarks | SF-10, SF-11 | `NOT_STARTED` | — | — |
| SF-13 | Media Asset Model & Cloudflare Provider Boundary | SF-03, SF-06, SF-08 | `NOT_STARTED` | — | — |
| SF-14 | Direct Upload, Protected Delivery & Media Lifecycle | SF-13, SF-08 | `NOT_STARTED` | — | — |
| SF-15 | Transcription, Chapters, Summaries & AI Baseline | SF-13 | `NOT_STARTED` | — | — |
| SF-16 | Community & Moderation | SF-05, SF-06 | `READY` | — | Dependencies approved; user authorizes implementation of all newly READY concerns. |
| SF-17 | Analytics Events & Transactional Publication | SF-05, SF-06 | `READY` | — | Dependencies approved; user authorizes implementation of all newly READY concerns. |
| SF-18 | Discovery, Search, Recommendation & Editorial | SF-06, SF-12, SF-17 | `NOT_STARTED` | — | — |
| SF-19 | Offline / Downloads & Legacy DRM De-risking | SF-08, SF-14 | `NOT_STARTED` | — | — |
| SF-20 | Core Refactor Hardening Gate | SF-02, SF-03, SF-04, SF-05, SF-06, SF-07, SF-08, SF-09, SF-10, SF-11, SF-12, SF-13, SF-14, SF-15, SF-16, SF-17, SF-18, SF-19 | `NOT_STARTED` | — | — |
| SF-21 | Application Compute & Worker Topology | SF-20 | `NOT_STARTED` | — | — |
| SF-22 | Database, Cache, Broker & Search Hosting | SF-20 | `NOT_STARTED` | — | — |
| SF-23 | Edge, CDN & Object-Storage Security | SF-14, SF-20 | `NOT_STARTED` | — | — |
| SF-24 | Networking, Secrets & Least Privilege | SF-21, SF-22, SF-23 | `NOT_STARTED` | — | — |
| SF-25 | IaC, CI/CD, Releases & Environments | SF-21, SF-22, SF-23, SF-24 | `NOT_STARTED` | — | — |
| SF-26 | Backup, Restore & Disaster Recovery | SF-22, SF-25 | `NOT_STARTED` | — | — |
| SF-27 | Observability, Reliability, Capacity & FinOps | SF-21, SF-22, SF-23 | `NOT_STARTED` | — | — |
| SF-28 | Production Infrastructure Acceptance Gate | SF-21, SF-22, SF-23, SF-24, SF-25, SF-26, SF-27 | `NOT_STARTED` | — | — |
| SF-29 | Advanced Player | SF-28 | `NOT_STARTED` | — | — |
| SF-30 | Smart Library & Smart Downloads | SF-29 | `NOT_STARTED` | — | — |
| SF-31 | Cross-Device Playback & Active Session | SF-30 | `NOT_STARTED` | — | — |
| SF-32 | RSS & OPML Portability | SF-31 | `NOT_STARTED` | — | — |
| SF-33 | Clips & Quote Cards | SF-32 | `NOT_STARTED` | — | — |
| SF-34 | Video Podcasts & Media Variants | SF-33 | `NOT_STARTED` | — | — |
| SF-35 | Football Intelligence & Content Knowledge Graph | SF-34 | `NOT_STARTED` | — | — |
| SF-36 | Semantic Search / Ask SANFootball | SF-35 | `NOT_STARTED` | — | — |
| SF-37 | Intelligent Notifications, Personalised Home & Highlights | SF-36 | `NOT_STARTED` | — | — |
| SF-38 | Creator & Subscription Conversion Analytics | SF-37 | `NOT_STARTED` | — | — |
| SF-39 | Networks, Creator Teams & Advanced Commercial Packaging | SF-38 | `NOT_STARTED` | — | — |
| SF-40 | Live Podcasting | SF-39 | `NOT_STARTED` | — | — |
| SF-41 | Matchday Rooms, Chapters & Listen-Around-the-Match | SF-40 | `NOT_STARTED` | — | — |
| SF-42 | Listener Stats, Annual Recap & Achievements | SF-41 | `NOT_STARTED` | — | — |
| SF-43 | Connected Devices & Low-Bandwidth Experience | SF-42 | `NOT_STARTED` | — | — |
| SF-44 | Transcript Translation, Accessibility & Creator AI | SF-43 | `NOT_STARTED` | — | — |
| SF-45 | Final System Hardening, End-to-End Acceptance & Cleanup | SF-44 | `NOT_STARTED` | — | — |

## Baseline / Inventory

- Snapshot: 2026-10-11; repository `/workspace/90-Nutmegs-db`; branch `work`; HEAD `e24ff2e9c9ae7ecb563215f1cfc4f1b6e6687c6e`. One worktree; initial status including untracked files was empty. No pre-existing user changes were overwritten.
- At SF-00 capture, no concern was approved and SF-01/SF-02 were `NOT_STARTED`. SF-00 was subsequently approved by the user on 2026-10-11. Its snapshot documents remain historical evidence.
- Read root protocol, orchestrator, SF-00 brief, source map and only mapped master sections: A.3–A.8; Part I §50 Phase 0, §53, §§67–68; Part II Phase 0 and §68. No additional master section loaded. Explicit SF-00 scope/root protocol bound older whole-master/configuration/test-expansion instructions; implementation is reserved for owning concerns.
- 540 tracked starting files; 478 Python files; 67 Django registrations (48 repository / 19 dependency); 88 repository models plus documented abstract bases; 49 numbered migrations; 174 non-admin URL leaves; 28 test-prefixed modules including runner/scaffolds; six Celery tasks.
- Python 3.14.8; Django 5.2.17; DRF 3.18.0; Celery 5.6.3; 32 default dependencies, optional media/ML/dev extras; 187 lock entries and 117 default/dev installed distributions. `pycflare` pinned to `f214c80de3843d47f0593386a60169c77e8bc801`.
- Evidence: [current architecture](docs/architecture-current.md), [registry/source inventory](docs/baseline-inventory.md), [validation commands/results](docs/baseline-validation.md), [SF-00 design note](docs/refactor-plan.md), updated repository README. These documents are evidence/design, not competing trackers.
- SF-00 made no code, test, settings, dependency, migration, provider, public contract or infrastructure implementation change. No persistent database was touched; later review packets below describe their own patches.

## Completed

SF-00 characterization and applicable baseline checks are complete; review packet is ready. Changed files: `README.md`, this ledger, `docs/architecture-current.md`, `docs/baseline-inventory.md`, `docs/baseline-validation.md`, and `docs/refactor-plan.md`. SF-00 was approved by the user on 2026-10-11; see the approval log.

Acceptance gate: baseline commands/results known; existing owners and unresolved duplicates mapped; user state preserved; infrastructure/security/capacity risks recorded; next safe concerns identified without starting them. Failed pre-existing checks remain visible and are not claimed as passing. Reviewer steps and reproduction are in [baseline-validation.md](docs/baseline-validation.md#reviewer-reproduction).

### SF-01 review packet (2026-10-11)

- Implemented: 23 new tests (14 URL/HTTP ownership contracts, five supported listener journeys, four transaction/publication tests), explicit zero-query/cache liveness coverage; stale branding assertion and scoped formatting corrected. A legacy test no longer requires the known processed-on-transcription-failure state; logging/cleanup coverage remains.
- Exact files: `app/conf/test_api_contracts.py`, `app/conf/test_listener_journeys.py`, `app/apps/media/audio/test_dispatch.py`, `app/conf/test_health.py`, `app/apps/media/audio/tests.py`, `app/api/rest/web/apps/podcasts/tests.py`, `docs/testing.md`, this ledger. SF-00 snapshot documents unchanged.
- Owners/decisions: preserve current AccessPolicy, billing, media, Queue, PlayBack and migration implementations; add tests at real HTTP/ORM and transaction boundaries. No feature implementation, migrations/backfills, API/runtime behavior change or legacy removal. Test-only rollback; no data rollback. Query/concurrency/provider/storage/cost behavior unchanged.
- Validation: complete coverage suite PASS (298 tests, 28.553s; 62%, above 50% threshold); `pip check`, compileall, workflow scoped Ruff format/lint, six-file mypy, Django check, synthetic production deploy check, migration drift, OpenAPI and coverage XML PASS. New/updated focused files Ruff format/lint PASS; `git diff --check` PASS. Existing schema warnings remain. Commands match `docs/baseline-validation.md` with output directory `/tmp/sf01-checks`. Unchanged dependencies were not re-audited; SF-00's 17-advisory failure remains SF-03 work.
- Newly reproduced defects: actual login session rotation leaves anonymous queue unmerged; anonymous queue writes return 401; follow POST mutates then fails serialization; followed-show library calls an absent manager; partial playback payload raises KeyError; dashboard PATCH audio action is shadowed. These are intentional later-owner correction targets, not passing assertions endorsing defects. See `docs/testing.md` for reproducible triggers and scope limits.
- Limits: real providers/workers, browser login and PostgreSQL concurrency remain unverified. No new operational telemetry or entitlement/privacy behavior change; tests strengthen isolation/denial coverage.
- Reviewer: inspect the eight-file SF-01 scope; run `uv run --locked python app/manage.py test --settings=conf.settings.test` and workflow/focused lint checks; review `docs/testing.md` for covered vs defective/absent scenarios. Only human approval may unlock dependent work; SF-04/SF-05 also require SF-02 approval.

### SF-02 review packet (2026-10-11)

- Implemented: canonical environment parsing with value-free startup failures; production host/HTTPS-origin/PostgreSQL/Redis/timeout/TTL validation; required public/Giffy endpoints; Django key rotation fallbacks; explicit trusted-proxy and verified-TLS HSTS rollout; local browser cookie/origin consistency; test trust/secret isolation; final-output redaction for application, Django, Celery/task and multiprocessing logs, including exceptions. Environment examples, ignore rules, documentation and existing CI scopes updated.
- Exact files (15): `.env.example`, `.github/workflows/backend.yml`, `.gitignore`, `README.md`, `SANFOOTBALL_IMPLEMENTATION_STATUS.md`, `app/conf/settings/base.py`, `app/conf/settings/development.py`, `app/conf/settings/production.py`, `app/conf/settings/test.py`, `app/conf/settings/environment.py`, `app/conf/logging.py`, `app/conf/test_configuration.py`, `app/conf/test_logging.py`, `app/conf/tests.py`, `docs/configuration.md`.
- Owners/architecture: retain the explicit settings modules and entrypoint/compatibility aliases, python-decouple environment precedence, existing `CloudflareMediaConfig`/pycflare boundary and all domain owners. Add no parallel state, settings service, dependency or provider feature. No API route/serializer/entitlement changes. No migration, backfill, persistent DB operation or legacy-code deletion.
- Compatibility/rollback: production now requires explicit HTTPS `MAIN_PUBLIC_BASE_URL` and `GIFFY_API_BASE_URL`; malformed trust/service values and obvious secret placeholders fail startup. Existing TLS-terminating proxies must explicitly enable `TRUST_PROXY_SSL_HEADER` only after header stripping/network trust verification, otherwise redirects can loop. HSTS now requires explicit verified rollout (defaults 0/false/false). Development history/queue cookies support HTTP. Django/Celery logs use redacted stderr instead of Django default error-email handlers. Roll back code and configuration together; browser HSTS persists independently. Detailed rollout/rotation procedure: `docs/configuration.md`.
- Validation: 33 new configuration/logging tests PASS; full coverage suite PASS (331 tests, 37.549s; 63%, threshold 50%); workflow `pip check`, compileall, Ruff format/lint (including new modules), six-file mypy, test Django check, synthetic production deploy check, migration-drift check, OpenAPI and coverage XML PASS. Explicit development Django check PASS. Production/schema checks retain 45 unique schema warnings (schema generation 84 total, zero errors). Commands are exactly the workflow with isolated outputs under `/tmp/sf02-checks`; focused command: `python app/manage.py test conf.test_configuration conf.test_logging --settings=conf.settings.test`. No dependency change: inherited 17-advisory audit failure remains SF-03; not rerun or represented as passing.
- Security/operations: malformed startup values omit supplied data and parser exception chains; logs mask configured secrets, structured sensitive fields, auth headers, signed media capabilities, private keys and webhook bodies. Real Django/Celery logging setup is exercised in development/test/production child processes. Rotation accepts prior Django signatures. Formatter does no DB/network I/O, leaves shared LogRecords untouched and rereads canonical settings; runtime cost scales with log size/settings and was not load-tested. Unlabelled sensitive data, external handlers and direct stdout/stderr remain caller responsibilities.
- Infrastructure/performance: no query, transaction, retry, concurrency, provider-domain, queue-routing, storage topology, backup or cost change. No real provider/worker/deployment connection attempted. Live PostgreSQL locks, proxy/domain coverage, least privilege, provider credentials and HSTS rollout remain operational verification for later owning concerns.
- Secret hygiene: inspected configuration/documentation/logging examples contain placeholders or synthetic test values only. Seven high-confidence credential/private-key patterns found no matches across 553 current nonignored files and 573 selected source/config/documentation blobs from all four reachable commits; only metadata was emitted. This is a limited pattern review, not an exhaustive historical credential or deployed-secret audit. `.env` variants are ignored and `.env.example` remains tracked.
- Preservation: all pre-existing files outside the ten edited SF-02 paths match the SF-02 start hashes, including all SF-01 implementation and four approved SF-00 snapshot documents. README/ledger retain baseline context while documenting current changes. No master/checksum, dependency, model or migration file changed.
- Reviewer steps: (1) review the 15-file scope and `docs/configuration.md`; (2) run `uv run --locked python app/manage.py test conf.tests conf.test_configuration conf.test_logging --settings=conf.settings.test`, then the full suite and workflow checks; (3) confirm malformed values and actual worker logging are covered by the new tests; (4) assess required endpoint/proxy/HSTS compatibility against deployment configuration without copying secrets; (5) approve or return SF-01 and SF-02 independently in this ledger. Deployment itself has not been performed.
- Next after human approval: SF-03 is eligible after SF-02 approval; SF-04/SF-05 require both SF-01 and SF-02 approval. SF-20 also lists SF-02 but remains gated by SF-03–SF-19. No downstream work is started or self-approved.

### SF-03 review packet (2026-10-12)

- Implemented: explicit Celery `celery`/`media`/`bulk` queues and fixed registered beat entry points; independent web, ordinary/media/bulk worker, scheduler and admin commands; bounded concurrency/prefetch/task limits and direct TERM handling; Gunicorn redaction through the approved formatter. Web entrypoints and recommendation command discovery are tested without heavyweight imports, database queries, networking or subprocess work. ML imports/artifact-directory creation now occur only in explicit command execution.
- Exact files (16): `pyproject.toml`, `uv.lock`, `.github/workflows/backend.yml`, `README.md`, this ledger, `app/conf/settings/base.py`, `app/conf/task_queues.py`, `app/conf/tasks.py`, `app/conf/gunicorn_logging.py`, `app/conf/test_task_queues.py`, `app/conf/test_runtime_isolation.py`, `app/run_process.py`, `app/apps/recommendation/management/commands/generate_dataset.py`, `app/apps/recommendation/management/commands/train_recommenders.py`, `docs/dependencies.md`, `docs/runtime.md`.
- Owners/decisions: existing Celery, Django settings and health probes remain canonical. Add Gunicorn as the missing production WSGI server; retain immutable pycflare commit/extras. Preserve existing six task identities and schedule keys/cadences; register three fixed maintenance wrappers instead of exposing arbitrary management commands. Preserve default queue `celery` for compatibility. No domain owner, schema, entitlement or recommendation algorithm redesign.
- Dependencies: remove unused gevent/honcho/python-multipart/Torch/Whisper declarations and redundant direct Clerk backend/PyYAML requirements; retained transitives remain locked. Introduce `transcription-workers`, retain compatible `media-workers` alias and existing recommendation/dev extras. Core has 28 direct requirements; lock has 142 package entries. Upgrade PyJWT 2.13.0→2.15.1 and urllib3 2.7.0→2.8.0 with resolver security floors. Actual locked optional SDK/numerical imports and small NMF/FAISS/joblib exercises passed on CPython 3.14.8 Linux x86_64 in an isolated environment; no provider calls/model downloads. Runtime matrix and reproduction are in `docs/dependencies.md`.
- Validation: full suite PASS (343 tests, 48.781s; 64% coverage); 45-file workflow Ruff format/lint, six-file mypy, compileall, installed dependency check, test/development Django checks, synthetic production startup, migration drift, OpenAPI, coverage threshold/XML and offline `uv lock --check` PASS. Web/combined-worker dependency audits PASS, no known vulnerabilities; immutable VCS pycflare is skipped by the scanner. Initial resumed audit attempts failed solely because the home cache is read-only; reruns with explicit writable cache passed. Existing OpenAPI warnings remain. Current evidence is under `/workspace/.sf-evidence/sf03`; the earlier environment's `/tmp` evidence was ephemeral and was lost on resume, while source files persisted.
- Compatibility/operations: start new queue consumers before producers, drain legacy queued media jobs with the previous fully equipped worker, and keep exactly one beat scheduler. Repaired beat now makes existing license expiry/device revocation/package cleanup jobs callable: inspect staging effects and existing schedules before production activation. Gunicorn sync web defaults to two workers; media/bulk concurrency defaults one; commands expose bounded overrides. Prefork RSS recycling is not an OS memory cap. Task limits do not prove FFmpeg descendant termination, temporary-disk quotas or provider retry safety. Current audio/transcription stays in one media task; separate AI task lifecycle remains SF-15.
- Migrations/backfills/rollback: none created or applied to persistent data. No API route/client payload change. Roll back code/lock/process routing together after draining affected queues; old dependency lock reintroduces known audit findings. Existing django-celery-beat rows retain their keys/cadences; no automatic DB cleanup or deployment performed.
- Query/performance/security: web startup has explicit zero-I/O/import guards; no domain query/concurrency behavior changed. Separate pools permit independent capacity. Logs reuse secret redaction; no raw credential values added. Real broker durability, in-flight failure/retry behavior, provider connectivity, production resource limits and throughput remain unverified. GC suppressing storage-delete failures, transcription placeholder/normalization bugs and dormant training-on-import code are recorded for SF-19/SF-15/SF-18.
- Legacy removal: obsolete dependency declarations/transitive stack and unregistered generic beat targets removed; existing business implementations retained. No model/route/data deletion.
- Reviewer steps: (1) review `docs/runtime.md` and `docs/dependencies.md`, especially queue cutover and maintenance activation; (2) run `uv sync --locked --extra dev`, `uv run --locked python app/manage.py test conf.test_runtime_isolation conf.test_task_queues --settings=conf.settings.test`, then the full suite/workflow checks (local socket permission required for Gunicorn tests); (3) run both documented profile audits; (4) inspect dry-run role commands and actual deployment resources before deploying. Only human approval may unlock SF-13/SF-20, which still require their other dependencies.

### SF-04 review packet (2026-10-12)

- **Concern/status:** SF-04 — Legacy Framework & API Structure Removal; READY_FOR_REVIEW, not approved.
- **Implemented/owners:** ordinary Django domain AppConfigs and feature-local URL modules replace the Oscar-derived framework. Django's app registry owns runtime model lookup; direct imports own known classes. API packages are no longer registered apps. Entitlement representation selection stays in the memberships API rather than domain startup. Existing `/api/rest/` versioning is retained. See [API structure](docs/api-structure.md).
- **Compatibility/migrations/rollback:** all 174 non-admin routes retain paths, callbacks, action maps and permissions; reverse aliases, 107 model/table identities and 84 admin registrations are preserved. App registrations fall from 67 to 47. No data migration/backfill or client deprecation. Deploy/rollback the complete application artifact so settings and URL modules match. Internal imports of deleted classes are retired after repository caller migration.
- **Tests/checks:** full coverage suite **350 PASS** (49.060s); workflow Ruff format/lint (91 files), six-file mypy, compile, installed graph, Django test/production checks, no migration drift, OpenAPI generation and both dependency audits **PASS**. Schema remains 84 warnings (45 unique), zero errors. Seven new structure/model-lookup tests verify startup without legacy imports, route/registry preservation and runtime lookups. Existing HTTP journeys and queue reverse aliases pass. First full run failed one snapshot test because DRF mutates action maps by adding implicit HEAD after GET; copied-map normalization fixed it and the complete suite was rerun successfully. Expanded legacy caller lint has pre-existing findings, with no new findings; no unrelated cleanup sweep.
- **Query/performance/concurrency:** no business queries, writes, transaction semantics or concurrency state added. Queue/flatpage runtime lookup tests assert one query; startup no longer imports the API layer. No duplicate mutable owner.
- **Security/privacy/entitlements:** permissions and representations preserved; no new authorization bypass or entitlement decision. Existing dashboard exposure and generic entitlement representation concerns belong to SF-05. Public behavior is not asserted to satisfy later domain requirements.
- **Operations/observability/infrastructure:** no provider, storage, broker, worker, backup, log or cost topology changes. Startup/check probes cover normal boot. Domain signals remain registered; no admin registration is lost.
- **Legacy removed:** 20 API routing AppConfigs and 19 obsolete default_app_config declarations; core application/loading/exceptions, duplicate api.rest.core loader and api.rest.utils.loading; dead dynamic-loader/logout-cookie settings; unused loader imports and speculative non-existent episode/course serializer registrations. Domain/provider/data implementations remain with their later owners.
- **Risks/deferred:** dashboard audio duplicate DELETE/PATCH remains a characterized SF-14 behavior; schema warning remediation belongs to feature owners. No physical move of feature serializer/view modules is needed because the existing clear feature structure is retained. Master provenance discrepancy remains unresolved as previously recorded.
- **Reviewer steps:** (1) inspect exact file list below and docs/api-structure.md; (2) run `uv run --locked python app/manage.py test conf.test_api_structure conf.test_model_loading conf.test_api_contracts conf.test_listener_journeys apps.queue --settings=conf.settings.test`; (3) run the backend workflow commands including full coverage and schema; (4) verify historical application-name reverse aliases and no model migration; (5) review then explicitly approve or request changes.
- **Next after approval:** SF-06 becomes READY only after human SF-04 approval. SF-20 remains gated by its full dependency set. SF-05 is independently authorized by already-approved SF-01/SF-02.
- **Exact changed/added files (relative to SF-04 start):**

```text
.github/workflows/backend.yml
README.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
app/api/__init__.py
app/api/rest/__init__.py
app/api/rest/dashboard/__init__.py
app/api/rest/dashboard/apps/__init__.py
app/api/rest/dashboard/apps/match/__init__.py
app/api/rest/dashboard/apps/match/urls.py
app/api/rest/dashboard/apps/memberships/__init__.py
app/api/rest/dashboard/apps/memberships/serializers.py
app/api/rest/dashboard/apps/memberships/urls.py
app/api/rest/dashboard/apps/persons/__init__.py
app/api/rest/dashboard/apps/persons/urls.py
app/api/rest/dashboard/apps/podcasts/__init__.py
app/api/rest/dashboard/apps/podcasts/urls.py
app/api/rest/dashboard/apps/promotions/urls.py
app/api/rest/dashboard/apps/region/__init__.py
app/api/rest/dashboard/apps/region/urls.py
app/api/rest/dashboard/apps/urls.py
app/api/rest/dashboard/urls.py
app/api/rest/dashboard/utils.py
app/api/rest/exceptions.py
app/api/rest/fields.py
app/api/rest/urls.py
app/api/rest/web/__init__.py
app/api/rest/web/apps/__init__.py
app/api/rest/web/apps/comments/__init__.py
app/api/rest/web/apps/comments/urls.py
app/api/rest/web/apps/comments/views.py
app/api/rest/web/apps/media/__init__.py
app/api/rest/web/apps/media/audio/__init__.py
app/api/rest/web/apps/media/audio/urls.py
app/api/rest/web/apps/media/offline/__init__.py
app/api/rest/web/apps/media/offline/urls.py
app/api/rest/web/apps/media/streaming/__init__.py
app/api/rest/web/apps/media/streaming/urls.py
app/api/rest/web/apps/media/urls.py
app/api/rest/web/apps/podcasts/__init__.py
app/api/rest/web/apps/podcasts/urls.py
app/api/rest/web/apps/profile/__init__.py
app/api/rest/web/apps/profile/urls.py
app/api/rest/web/apps/queue/__init__.py
app/api/rest/web/apps/queue/urls.py
app/api/rest/web/apps/urls.py
app/api/rest/web/serializers/comments.py
app/api/rest/web/urls.py
app/api/urls.py
app/apps/accounts/apps.py
app/apps/analytics/apps.py
app/apps/billing/apps.py
app/apps/billing/forms.py
app/apps/category/apps.py
app/apps/comments/apps.py
app/apps/config.py
app/apps/forum/apps.py
app/apps/forum/managers.py
app/apps/match/apps.py
app/apps/media/apps.py
app/apps/media/audio/apps.py
app/apps/media/chapters/apps.py
app/apps/media/images/apps.py
app/apps/media/transcription/apps.py
app/apps/media/video/apps.py
app/apps/memberships/apps.py
app/apps/persons/apps.py
app/apps/posts/apps.py
app/apps/posts/podcasts/apps.py
app/apps/posts/polls/apps.py
app/apps/promotions/apps.py
app/apps/queue/apps.py
app/apps/queue/models.py
app/apps/recommendation/apps.py
app/apps/region/apps.py
app/apps/region/leagues/apps.py
app/apps/region/leagues/clubs/apps.py
app/apps/tactics/apps.py
app/apps/thumbnail/apps.py
app/conf/fixtures/api_structure_sf04.json
app/conf/settings/base.py
app/conf/test_api_structure.py
app/conf/test_model_loading.py
app/conf/urls.py
app/core/compat.py
app/core/validators.py
docs/api-structure.md
```

- **Exact deleted files:**

```text
app/api/config.py
app/api/rest/config.py
app/api/rest/core.py
app/api/rest/dashboard/apps/config.py
app/api/rest/dashboard/apps/match/apps.py
app/api/rest/dashboard/apps/memberships/apps.py
app/api/rest/dashboard/apps/persons/apps.py
app/api/rest/dashboard/apps/podcasts/apps.py
app/api/rest/dashboard/apps/promotions/apps.py
app/api/rest/dashboard/apps/region/apps.py
app/api/rest/dashboard/config.py
app/api/rest/utils/loading.py
app/api/rest/web/apps/comments/apps.py
app/api/rest/web/apps/config.py
app/api/rest/web/apps/media/apps.py
app/api/rest/web/apps/media/audio/apps.py
app/api/rest/web/apps/media/offline/apps.py
app/api/rest/web/apps/media/streaming/apps.py
app/api/rest/web/apps/podcasts/apps.py
app/api/rest/web/apps/profile/apps.py
app/api/rest/web/apps/queue/apps.py
app/api/rest/web/config.py
app/core/application.py
app/core/exceptions.py
app/core/loading.py
```

### SF-05 review packet (2026-10-13)

- **Concern/status:** SF-05 — Identity, Authentication & Authorization Foundation; READY_FOR_REVIEW, not approved. SF-01/SF-02 user approvals recorded; the authorized SF-03/SF-04/SF-05 set is complete. Repository remains `work` at `e24ff2e`; existing approved and pending-review patches preserved. No commit, deployment, real provider call or persistent database mutation performed.
- **Implemented/owners:** existing `users.ClerkUser` and its unique nullable `clerk_user_id` remain canonical. Repository-owned `accounts.identity` verifies through the pinned Clerk SDK on every request, resolves only verified subject IDs, rejects email collisions without relinking, and safely converges first-use mapping through the existing unique constraint. Local staff/superuser/suspension state and AccessPolicy are independent of provider claims. Common bearer-first/session-CSRF behavior, malformed bearer rejection and sanitized outage handling are retained and exercised with real signed JWTs. Local middleware replaces SDK identity synchronization/cache behavior; only per-request result reuse remains.
- **Authorization/audit:** all interactive dashboard routes, including router roots/schema pages, require active local staff. This preserves the existing content-operator role; existing object/model checks remain additional requirements. Commercial reads require active staff and every commercial mutation, including `add_feature`, requires active staff superuser. No new job-title scheme or role table. The existing Giffy signature callback is explicitly separate. Successful dashboard mutations write bounded actor/model/object/method/action/route metadata to existing Django admin LogEntry in the same transaction; failure or audit insertion failure rolls back database writes. Existing Django admin audits local privilege edits.
- **Privacy/session:** follower lists removed from dashboard and nested podcast/entitlement projections; counts retained. Unknown generic entitlement targets return only opaque IDs without fetching/stringifying them; public membership/subscription fields are allowlisted. Existing public user privacy projection preserved. Original server-known anonymous session identity now reaches the queue receiver after real Django login rotation, with no client-submitted IDs or authenticated-user queue takeover.
- **Compatibility/migrations/rollback:** no schema migration, backfill or replacement user/role/audit model. Existing model/admin identities, routes/names/action maps remain. Intentional security changes restrict formerly open dashboard sports endpoints, close commercial action override, remove follower fields and unsafe generic target data, and stop automatic email identity linking. SF-04's historical fixture is unchanged; its test enumerates only SF-05's permission/root-class delta. Deploy local identity service, middleware and adapter together. Whole-artifact rollback would restore prior security weaknesses; prefer a forward fix or disable affected routes. No unsafe compatibility alias supplied.
- **Tests/checks:** complete suite **381 PASS**, 49.381s, **65% coverage**; coverage threshold/XML PASS. Workflow compile, installed dependency graph, 108-file Ruff lint/format, six-file mypy, test and synthetic-production Django checks, no migration drift and OpenAPI generation PASS. Formatting initially required one test adjustment after auto-fix; final format rerun PASS. Final middleware review restricts anonymous session capture to login POSTs so read-only sessions stay lazy. Its initial whole-request probe exposed the pre-existing SESSION_SAVE_EVERY_REQUEST behavior; the focused regression isolates middleware with automatic resaving disabled, and the final complete suite was rerun. Operational probes should omit browser cookies. OpenAPI retains 84 warnings (45 unique), zero errors. Thirty-one new tests plus updated auth tests cover actual SDK signed JWT verification (bad signature/expiry/nbf/audience/party), case-insensitive bearer and cookie/session precedence, CSRF, local suspension/privileges, ID uniqueness/first-use race window, all 172 DRF credential contracts, every interactive dashboard route's denial policy, commercial audit/rollback, privacy, and real login rotation. Final evidence: `/workspace/.sf-evidence/sf05/checks`.
- **Dependency audit distinction:** current locked web profile audit PASS, no known vulnerabilities (immutable pycflare VCS skip retained). Current worker-profile reruns are **INCONCLUSIVE / external failure**: initial PyPI timeout, then HTTP 503 from `https://pypi.org/pypi/openai/3.5.0/json`; no vulnerability result is claimed. The identical `pyproject.toml`/`uv.lock` worker profile passed SF-04 and those files are hash-verified unchanged. This does not block SF-05 code review; reviewer must retry the worker audit before release. No dependency was changed to work around the outage.
- **Query/concurrency/performance:** established identity lookup is one indexed DB query per request after verification; no token-to-user cache can outlive JWT expiration or local suspension. First-use inserts use a transaction and unique-ID constraint, with retry-winner lookup. Tests cover uniqueness and an interleaved first-use lookup, not real PostgreSQL concurrent transactions. JWT/JWKS verification network cost and pre-DRF-throttle abuse limits require staging/deployment measurements. Staff audit adds one write per successful mutation and cached content-type lookup. Existing provider-backed dashboard handlers now hold the audit transaction while running; provider lifecycle/async redesign remains SF-14/SF-18.
- **Security/privacy/operations limits:** no entitlements are granted from claims; secrets/provider exception details are omitted from new logs. Metadata-only audit persists in the existing admin store. This does not roll back external provider/storage side effects. Dynamic-queryset views without a declared model retain view/route/target audit metadata without an admin object link. Remote Clerk revocation timing, tenant configuration, network failure, PostgreSQL races and legal retention/deletion policy still require staging/operator evidence. No new infrastructure, queue, storage, backup or service provisioned; audit growth and verification traffic need SF-27 capacity review.
- **Legacy removed:** unused hardcoded job-title/owner permission classes and uncalled RoleAssignor module; live SDK email-linking/profile-overwrite/token-cache path replaced by canonical local mapping; generic all-fields/string entitlement fallback and follower-list projections removed. SDK package stays for verified authentication and existing user model. Domain models, migrations, queue ordering and provider implementations are preserved.
- **Deferred findings:** commercial PlanCreateSerializer treats a related manager as a list during response serialization (SF-07); new atomic audit wrapper rolls back that failed mutation, but serializer redesign is not implemented here. Anonymous queue mutation/concurrency/bearer-session merge remain SF-11; generic comment target policy remains SF-16. Existing offline device-wrapped key delivery is an intentional protected legacy contract, default-disabled, for SF-19 review; generic entitlement serialization can no longer expose it accidentally. Existing schema/master-provenance findings remain.
- **Reviewer steps:** (1) inspect exact files below and [identity/authorization runbook](docs/identity-and-authorization.md); (2) run its focused command for identity, endpoint contracts, staff, privacy, login and existing auth tests; (3) run `uv run --locked python app/manage.py test --settings=conf.settings.test` and all `.github/workflows/backend.yml` checks; (4) rerun `uv export --locked --no-dev --extra transcription-workers --extra recommendation-workers --no-emit-project --no-editable --no-hashes --output-file /tmp/worker-audit-requirements.txt` then `uv run --locked pip-audit --requirement /tmp/worker-audit-requirements.txt --no-deps --disable-pip`; (5) inspect minimal admin audit rows and review deployed staff flags/identity collisions; (6) perform described staging checks before deployment, then explicitly approve or request changes.
- **Next after approval:** SF-07, SF-10, SF-16 and SF-17 also require SF-06 approval; SF-20 requires its entire dependency set. None becomes READY from SF-05 completion alone. Only human approval changes dependency eligibility.
- **Exact changed/added files (38, relative to SF-05 start):**

```text
.github/workflows/backend.yml
README.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
app/api/rest/authentication.py
app/api/rest/dashboard/apps/match/urls.py
app/api/rest/dashboard/apps/match/views.py
app/api/rest/dashboard/apps/memberships/serializers.py
app/api/rest/dashboard/apps/memberships/urls.py
app/api/rest/dashboard/apps/memberships/views.py
app/api/rest/dashboard/apps/persons/urls.py
app/api/rest/dashboard/apps/persons/views.py
app/api/rest/dashboard/apps/podcasts/serializers.py
app/api/rest/dashboard/apps/podcasts/urls.py
app/api/rest/dashboard/apps/podcasts/views.py
app/api/rest/dashboard/apps/promotions/urls.py
app/api/rest/dashboard/apps/promotions/views.py
app/api/rest/dashboard/apps/region/urls.py
app/api/rest/dashboard/apps/region/views.py
app/api/rest/dashboard/audit.py
app/api/rest/dashboard/permissions.py
app/api/rest/dashboard/routers.py
app/api/rest/dashboard/urls.py
app/api/rest/web/serializers/membership.py
app/api/rest/web/serializers/test_authentication.py
app/apps/accounts/identity.py
app/apps/accounts/middleware.py
app/apps/accounts/session.py
app/apps/accounts/test_identity.py
app/apps/queue/signals.py
app/conf/settings/base.py
app/conf/test_api_structure.py
app/conf/test_endpoint_authentication.py
app/conf/test_identity_privacy.py
app/conf/test_login_identity.py
app/conf/test_staff_authorization.py
docs/api-structure.md
docs/identity-and-authorization.md
docs/testing.md
```

- **Exact deleted file:** `app/api/rest/dashboard/utils.py`.

### SF-06 review packet (2026-10-14)

- **Concern/status:** SF-06 — Podcast Content & Sports Metadata Canonicalization; READY_FOR_REVIEW, not approved. Only SF-06 became READY after the user's SF-03/SF-04/SF-05 approvals. Their exact review note is recorded below. Approved SF-00–SF-05 commit `7ba8eba69b3eb027cd4f1b1f60f3dc50c5f997bb` was pushed to [codex/approved-sf00-sf05](https://github.com/Leydotpy/90-Nutmegs-db/tree/codex/approved-sf00-sf05), and the remote SHA was verified. [Download approved code](https://github.com/Leydotpy/90-Nutmegs-db/archive/refs/heads/codex/approved-sf00-sf05.zip). SF-06 is a separate local, uncommitted patch on `codex/sf06-content-canonicalization`.
- **Implemented:** removed live category-to-plan derivation and implicit cheapest-paid-plan assignment; made category tiers optional historical metadata, read-only in dashboard/admin, and safe from plan CASCADE deletion. Preserved existing IDs/slugs and changed only new category slug inputs. Canonical Season owner/slug edits are rejected; dashboard updates revalidate a fresh locked row so stale metadata cannot undo a legacy-child graph move. Fixed sports code creation/retry/raw-import behavior for Region/Country/League/Team and registered the existing Match structure initializer with locking, replay reuse and raw-load protection. Extended the read-only content drift audit and added migration/API/transaction tests, documentation and CI scopes.
- **Owners/design:** retain `podcasts.Podcast/Season/Episode` and their tables, canonical release/visibility fields, existing AccessPolicy and existing structured Region/Country/League/Team/Player/Match relations. No second commercial/content/sports system. Existing canonical season expansion, root/child bridge, stable public route handling, deterministic artwork and historical slug reconciliation are VERIFIED EXISTING. One new schema expansion; no provider/domain package move or later concern implementation. Design/rollout: [content-canonicalization.md](docs/content-canonicalization.md).
- **Migrations/backfills:** new `category.0003_alter_category_slug_alter_category_tier` depends on `podcasts.0003`, changes `tier` to nullable SET_NULL and future slug generation, and preserves current associations/identifiers/access fields. Existing podcast 0002/0003 historical backfills remain unchanged and are verified by migration/reapply tests. No production/persistent database was modified; deployed apply-state and data still require restored-copy verification. Do not rerun historical data functions on current editorial rows. Reverse category schema requires explicit reconciliation of NULL tiers; do not invent plans or delete categories to satisfy the former NOT NULL constraint. Historical duplicate-slug repair is not losslessly reversible. Retain backup and identifier comparison evidence before rollout.
- **API/client compatibility:** routes, model IDs and existing slugs remain stable. Categories can be created without plans; historical `tier` is still returned (possibly null), but writes are ignored as read-only. New/ambiguous legacy exclusive requests without an existing explicit plan return a field validation error directing clients to canonical visibility/plan/release inputs; no silent category-derived or cheapest-plan grant. Legacy public release writes and existing explicit-plan/entitlement-only bridges remain. Direct Season owner/slug changes now return validation errors; legacy-child moves remain the explicit atomic graph transition. Avoid mixed old/new staff writers during cutover. Child rows and legacy release/tier projections are retained until deployed data/client verification permits contraction.
- **Tests/checks actually run:** focused `python app/manage.py test apps.posts.podcasts apps.category apps.region apps.match api.rest.dashboard.apps.podcasts api.rest.web.apps.podcasts --settings=conf.settings.test` **PASS**, 83 tests (12.847s). Full `coverage run app/manage.py test --settings=conf.settings.test --verbosity=1` **PASS**, 407 tests (46.349s), 66% coverage; report threshold and XML **PASS**. All 16 local workflow commands **PASS**: installed dependency graph, compile, 125-file formatting, scoped Ruff lint, six-file mypy, Django checks, synthetic production deploy check, model/migration drift, OpenAPI, both locked dependency exports/audits, complete suite and coverage outputs. Same dependency lock now passes both web and worker audits; immutable VCS pycflare is skipped by pip-audit. OpenAPI retains 84 warnings (45 unique), zero errors. Separate changed-model Ruff comparison **PASS**, zero old/new findings. An exploratory category-directory lint included four old historical-migration findings; those unchanged files are excluded from the scoped workflow and were not rewritten. Initial new-test import ordering was corrected before final checks.
- **Evidence/verification limits:** logs/results under `/workspace/.sf-evidence/sf06/checks`, focused log `/workspace/.sf-evidence/sf06/focused.log`; workflow commands use writable caches and local-socket/network permission for audits/Gunicorn tests. Python 3.14.8 was restored after the managed environment restarted. No real provider, PostgreSQL contention/load, live deployment, database backup/restore or production data audit has been run. The targeted read-only peer review found no blocking regression. Final whitespace, dependency eligibility and immutable-spec checks are recorded in the quality table.
- **Queries/performance/concurrency:** category edits no longer query categories/plans to infer access. Season metadata updates take a row lock and revalidate current identity; the legacy bridge retains its existing parent/Season locks. Match initialization uses the existing one-to-one Event, one Match row lock and bounded inserts; replay preserves recorded possession. Code candidates retry at most 100 times; DB uniqueness remains authoritative for concurrent Region/Country/League/Team writes. SQLite proves rollback/replay and historical migrations, not PostgreSQL contention. Existing broader content read/N+1 optimizations remain SF-18; no unbounded new read path is introduced.
- **Security/privacy/entitlements:** explicit Episode fields and the canonical policy remain authoritative. Taxonomy changes and historical category-plan deletion cannot change an explicit Episode plan. Ambiguous legacy exclusive writes fail validation; no implicit access widening. Entitlement-only legacy round-trips retain their restriction. Existing staff/audit authorization and protected-media boundaries are preserved; no new sensitive payload/log/identifier exposure.
- **Operations/infrastructure/provider/queue/storage/backup/cost:** no new service, provider call, task, queue or media storage topology. Content audit adds orphan-child owner, nonroot Season owner and published PLAN-without-plan counts; `--fail-on-drift` returns nonzero after JSON output. It never mutates data. Normal Match creation adds the already-intended structural rows; API/admin transactions include these writes. Standalone ORM callers must wrap Match creation in an outer atomic block for all-or-nothing creation. Old/raw-import Matches are not backfilled with invented score state. Operational rollout/rollback and audit steps are documented; no production cost/load claims.
- **Legacy removed:** live `Episode.get_highest_plan_in_categories`, the category-derivation switch and implicit fallback plan selection; recursive Region save and unnecessary Country post-insert update; broken recursive collision retry; dormant non-idempotent Match initializer body. No historical migration, URL, content row, table, legacy child bridge or compatibility data deleted.
- **Risks/deferred:** real target data/restore/locks need deployment verification; tierless categories prevent an unprepared schema rollback; raw/bulk ORM edits bypass operator validation; concurrent admin graph edits need operational care. Old Matches lacking Event and existing team-edit/partial Match update defects remain sports followup (SF-35/SF-40), not a live-feature implementation here. Existing Player post-save raw/zero-code handling remains a separate ingestion edge for SF-35; its identity/relations were preserved. Master provenance mismatch remains the recorded human/source-authority issue. The earlier SF-05 PyPI audit outage is resolved by this run, without changing its historical result.
- **Reviewer verification:** (1) download/test the approved GitHub checkpoint independently; (2) review the exact SF-06 files below and the content guide on this local branch; (3) run the focused command, full suite and workflow gates; (4) on a restored disposable target DB, capture IDs/slugs, inspect migration plan, apply the category expansion, run `audit_podcast_content --fail-on-drift`, and compare canonical owner/access/sports links and old URLs; (5) verify taxonomy edits never alter Episode access, ambiguous legacy exclusive inputs are rejected, Season owner/slug edits fail, and the legacy move carries Episodes; (6) explicitly approve or return SF-06. Only human approval unlocks more work.
- **Recommended next after approval:** SF-07 — Plan, Price, Subscription & Entitlement Models. Actual graph eligibility after SF-06 approval will be SF-07, SF-10, SF-16 and SF-17; SF-13 still needs SF-08, SF-18 still needs SF-12/SF-17, and SF-20 needs its remaining dependencies. No later concern has begun.
- **Exact changed/added files (27, relative to approved `7ba8eba`):**

```text
.github/workflows/backend.yml
README.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
app/api/rest/dashboard/apps/category/serializers.py
app/api/rest/dashboard/apps/podcasts/serializers.py
app/api/rest/dashboard/apps/podcasts/tests.py
app/apps/category/admin.py
app/apps/category/migrations/0003_alter_category_slug_alter_category_tier.py
app/apps/category/models.py
app/apps/category/test_migrations.py
app/apps/category/tests.py
app/apps/match/apps.py
app/apps/match/services.py
app/apps/match/signals.py
app/apps/match/tests.py
app/apps/memberships/policies.py
app/apps/posts/podcasts/management/commands/audit_podcast_content.py
app/apps/posts/podcasts/models.py
app/apps/posts/podcasts/services.py
app/apps/posts/podcasts/test_audit_podcast_content_command.py
app/apps/posts/podcasts/test_content_ownership.py
app/apps/region/leagues/clubs/receivers.py
app/apps/region/leagues/receivers.py
app/apps/region/receivers.py
app/apps/region/tests.py
app/utils/utils.py
docs/content-canonicalization.md
```

## Verified Existing Implementations

Verification is limited to cited source/constraints and the exercised tests; it does not approve the owning concern or certify complete master compliance.

| Existing implementation | Evidence verified under SF-00 | Limit / later owner |
|---|---|---|
| Explicit settings and startup guards | Existing settings tests; test check and synthetic production deploy check succeed | 45 schema warnings; live configuration unverified; SF-02 |
| Clerk bearer/session boundary, unique external-ID constraint and user projection | Existing behavior reused by SF-05; expanded real signed-token, DB uniqueness and privacy tests pass | Actual tenant/provider/PostgreSQL operational verification still required |
| Structured AccessPolicy and exact media capability binding | Membership/media tests pass; streaming/offline call policy | Cached compatibility paths remain; SF-08 |
| Podcast/Season/Episode canonical expansion and legacy bridges | SF-06 verifies existing migration/URL/ownership behavior, 83 focused tests and full 407-test suite | Compatibility data retained pending deployed-data/client verification |
| Canonical media tables and Cloudflare adapter primitives | Constraints, provider/upload/finalization/delivery tests and six-file mypy check pass | No runtime API callers for new services found; no real provider/cutover verification; SF-13/SF-14 |
| Playback bounds/identity and queue compatibility behavior | Existing progress/queue/merge tests pass | No PostgreSQL concurrency proof or complete canonical rewrite; SF-10/SF-11 |
| Billing transition locks and card obfuscation | Existing transition/refund/cancellation/ledger tests pass | Not provider/webhook fulfillment; SF-09 |
| Offline default-disable, signed-stream scope and callback restrictions | Existing offline/streaming tests pass | Legacy DRM remains present; SF-19 |
| Post-commit audio dispatch and safe readiness error responses | Source verifies Audio receiver uses `delay_on_commit` / `transaction.on_commit`; existing task/readiness tests pass | Dispatch semantics lack direct characterization; no durable outbox; one liveness branding assertion fails; SF-17/SF-01 |
| Existing CI and test discovery | 275 tests actually discovered; scoped lint/type/compile/drift checks pass | CI overall fails formatting, one test and audit; SF-01/SF-03 |

## In Progress

None. SF-06 reached READY_FOR_REVIEW on 2026-10-14; the following start/design notes are retained as history.

SF-06 started 2026-10-13 on `codex/sf06-content-canonicalization`, HEAD `7ba8eba`, clean worktree. SF-04 dependency APPROVED; all 46 graph rows checked and only SF-06 eligible. Approved code is pushed to [GitHub](https://github.com/Leydotpy/90-Nutmegs-db/tree/codex/approved-sf00-sf05); SF-06 remains separate and unapproved.

SF-06 initial design: retain canonical `podcasts.Podcast/Season/Episode`, explicit release fields, existing season migration/legacy URL bridges and structured sports owners. Characterize remaining category-to-plan derivation and metadata creation hooks, then remove live category commercial coupling with explicit content access input and safe schema expansion. Preserve historical migrations/public IDs; verify backfill and expose drift through the existing content audit. Repair only concrete sports metadata creation defects within SF-06. Commercial policy redesign remains SF-07/SF-08; advanced football/live features remain later concerns. Caller design: keep `Category.tier` nullable/read-only as a historical projection (`SET_NULL` on plan deletion), omit it from new slug generation, and keep historical migrations frozen. Remove live category-to-plan derivation and implicit paid-plan selection. Legacy public release inputs remain supported; ambiguous exclusive writes without an explicit existing plan require canonical visibility/plan/release inputs, preventing silent access widening. Legacy updates preserve existing explicit plans and entitlement-only protection. Keep direct Season owner/slug immutable after creation; refresh under a row lock on dashboard metadata updates to preserve concurrent legacy moves. Historical child bridges remain until deployed data/client verification permits removal. Historic designs below are retained as evidence.

User-approved SF-01/SF-02 recorded before implementation. All 46 dependencies were recomputed at selection: SF-03, SF-04, SF-05 became READY. That set was executed sequentially on `work`, preserving the reviewed working tree; subagents split tasks within the active concern only. Each new implementation ends at READY_FOR_REVIEW, without self-approval. SF-06 onward remain NOT_STARTED until their actual dependencies are approved. Start snapshot: `/tmp/sf03-start/hashes.json`, branch `work`, HEAD `e24ff2e`; existing 26 changed/untracked paths preserved.

Completed SF-01 design: extend the existing 275-test suite with missing meaningful HTTP journey/compatibility and transaction-publication coverage. Preserve AccessPolicy, billing, queue, playback, media and migration owners. Correct the stale health service-name assertion to the existing `90Nutmegs` response and its known formatting failure; do not rename runtime contracts. Existing policy/stream/download/billing/historical-migration tests are reused. No new webhook implementation, queue redesign, data migration or dependency upgrade is in scope. Unsupported target behaviors and known defects remain explicit later-concern change targets, not passing tests that enshrine defects. Source map read: Part I §35, §50 Phase 1, §55; Part II §47; additional Part I §16 matrix required by §35.5.

Completed SF-02 design (recorded before implementation): existing settings split, entrypoint defaults, production provider validation and aliases are verified and preserved. Tighten missing startup validation for hosts/origins/service URLs and numeric values with value-free errors; honor environment CORS/CSRF in development; document verified-TLS HSTS/proxy activation; add central configured logging redaction for secrets/capabilities and rotation-safe sourcing. Keep provider/domain behavior, databases, dependencies and migrations unchanged. Test synthetic malformed inputs and console/exception redaction, plus all existing settings/provider tests. Read mapped Part I §31, §§32.8–32.9; Part II §58, §79.3 and §84 Security. Snapshot current files/hashes before edits; SF-01 implementation stays untouched. SF-02 validation and review packet are now complete; no concern is active.

SF-03 design/start: preserve settings, health, Celery and domain ownership. Keep CPython 3.14 and immutable pycflare pin; verify and repair dependency groups/lock/security findings, prohibit heavyweight imports during web boot, supply separate bounded process commands and explicit task queues/scheduler targets. Preserve task identities; do not redesign media retry/business state or recommendation algorithms. Existing health/readiness and Celery shutdown semantics are reused and exercised. No schema/data migration. Read mapped Part I §§30,42–43; Part II §§38,44.2,57,59,77 only. Domain-specific idempotency/load/deployment work remains later scope.

SF-04 design/start: replace Oscar-derived routing AppConfigs with normal explicit Django URL includes and ordinary domain AppConfigs, preserving model app labels and existing URL namespaces/names/methods/permissions. The current `/api/rest/...` route family remains the supported compatibility contract; no new parallel `/api/v1` tree or domain redesign. Remove API-only registrations and migrate every dynamic class/model loader caller to explicit imports or Django's canonical app registry, then delete obsolete framework files. Keep feature-local API modules and move representation registration out of domain app startup. Capture all non-admin routes plus models/admin registrations before edits; test exact compatibility and existing HTTP journeys. Read only Part I §§25,47,50 Phase3,62–65. Adjacent domain/security defects remain later-owner findings unless routing migration requires correction. Start hashes under `/workspace/.sf-evidence/sf04` preserve approved work and SF-03 patch.

SF-05 design/start: retain AUTH_USER_MODEL and its existing unique Clerk-ID column as the single domain identity; no replacement user table or email-based automatic account linking. Preserve explicit bearer-first plus CSRF-protected browser-session compatibility, invalid-token fail-closed behavior and server AccessPolicy. Inspect the pinned SDK verification/sync/cache path; move unsafe synchronization behavior behind the accounts identity boundary where necessary. Protect all interactive dashboard endpoints with coherent active-staff/model-permission rules; provider-authenticated callbacks remain explicitly separate. Remove unused job-title permissions after tracing. Audit important staff mutations, prohibit sensitive generic representations and follower lists, and document endpoint authentication/privacy expectations. Preserve current public URLs and approved settings decisions. Fix only identity-session handoff needed for login; queue/domain redesign remains SF-11. Read Part I §§24,44 and Part II §§42–43 only. Baseline hashes at /workspace/.sf-evidence/sf05; no persistent database is modified.

## Deferred

No concern is marked `DEFERRED`. SF-06 is complete for review; adjacent findings remain assigned to their later owners and all SF-07+ concerns remain `NOT_STARTED` until dependencies are human-approved.

## Blocked

No SF-00 inventory dependency is blocked. Existing failing checks are characterized below, not presented as passing. Human review must resolve the master-spec checksum provenance discrepancy before relying on the claimed original-package checksum; SF-00 leaves both authority files untouched. This is not a competing architectural decision.

## Legacy Components Remaining

- SF-04 removed the Oscar framework and migrated all runtime callers; see its exact deletion manifest above.
- Membership plan/price coupling, Subscription `active` + `status`, legacy billing/card ledger and dormant entitlement helpers that reference absent `granted_by_purchase` and `Plan.slug` fields (SF-07/SF-09).
- Child-Podcast/parent/structure and release/exclusive/historical-category-tier projections remain for verified migration compatibility; live category commercial derivation removed in SF-06. Later contraction requires deployed data/client evidence (SF-08/SF-20).
- `PlayBack` in podcasts with anonymous IP identity; QueueItem `position` + `order`; PlayList and free subscriber M2Ms mixed into media/analytics (SF-10/SF-11/SF-12).
- Legacy Audio/Image/Video FileFields, boto3/S3/CloudFront code, local thumbnail/metadata paths, AWS/KMS custom offline packaging and Channels consumer (SF-13/SF-14/SF-19).
- Forum Discussion/Reply alongside routed generic Comment; no complete moderation owner (SF-16).
- Podcast query scoring, affinity/service/ML recommendation generations, legacy post recommender/dataset builder and local artifacts (SF-18).
- Dormant QuixStreams/thread event modules; no live caller or declared dependency found (SF-04/SF-17).
- Giffy remote banner integration plus older editorial list models; no provider or state migration in SF-00 (SF-18).
- Other domain deletions remain gated by their owning concerns and data/caller evidence.

## Data Migrations

| Migration / Backfill | Concern | State | Reversible / Rollback | Verification |
|---|---|---|---|---|
| SF-00 | SF-00 | None created/applied to persistent DB | Documentation revert only | Application/migration files preserved |
| SF-01 / SF-02 | SF-01 / SF-02 | No migrations/backfills | Test-only rollback for SF-01; coordinated code/config rollback for SF-02 | Full suite and model-drift check pass |
| SF-03 / SF-04 / SF-05 | SF-03 / SF-04 / SF-05 | No migrations/backfills; no persistent DB changed | Deploy complete artifacts; security rollback caveats in packets | Migration drift and full suites pass |
| New category 0003 taxonomy expansion | SF-06 | Added and tested on disposable test DB; no persistent migration | Reverse requires reconciling NULL tier values; prefer forward repair/verified restore | Historical ID/slug/M2M/access preservation test passes |
| Existing podcasts 0002 publication/access | SF-06/SF-08 | On disk; deployed apply-state unknown | Reverse data operation noop | Existing migration tests pass |
| Existing podcasts 0003 canonical seasons | SF-06 | On disk; deployed apply-state unknown | Reverse restores legacy child episode ownership; slug repair not losslessly undone | Historical graph/collision/reapply tests pass |
| Existing media 0002 asset/location/variant | SF-13 | On disk; no provider cutover verified | Schema rollback would remove new tables/data; do not infer production safety | Drift check and constraint tests pass |
| Existing generic object-ID migrations | SF-06/SF-16/SF-17 | IDs widened to text | Narrowing risks UUID/text loss; requires data inspection | No drift; PostgreSQL affinity join mismatch remains |
| Existing promotions 0002 and persons 0002 | SF-18/SF-06 | Historical removal/renaming operations | Promotion backfill reverse noop; removed historical data not proven recoverable | Graph loads; no restore claim |

## Backfills

| Backfill | Concern | State | Idempotent? | Verification |
|---|---|---|---|---|
| New SF-00 backfill | SF-00 | Not applicable | Not applicable | None run |
| Podcast publication/access and canonical season mapping | SF-06/SF-08 | Existing migration functions | Deterministic assignments/UUIDs; existing repeated-run cases tested, not a blanket operational retry claim | Existing tests pass; deployed data unknown |
| Remote banner fields | SF-18 | Existing promotion migration | Needs live-data/retry review before reuse | Source inspected; reverse is noop |

## Compatibility Routes / Contracts

| Contract | Concern | Compatibility Strategy | Removal/Review Condition |
|---|---|---|---|
| Current routes, action maps and admin/model identities | SF-04 / SF-05 | Historical SF-04 fixture preserved; explicit SF-05 permission and router-class delta | Current 381-test suite passes; no route deprecation |
| Identity and dashboard privacy/access | SF-05 | Bearer/session order retained; unique verified ID mapping; active-staff/superuser rules and safe projections | Intentional security restrictions; no unsafe legacy alias |
| Legacy child-Podcast routes and canonical Episode owner | SF-06 | Keep bridge services/projections; direct Season owner/slug immutable | Data reconciliation + client review |
| Category tier and legacy exclusive writes | SF-06 | Tier optional/read-only; explicit access inputs required for ambiguous exclusive writes | Update staff clients; avoid mixed-version writes |
| Episode publication/exclusive/category-plan fields | SF-08 | Policy plus explicit legacy synchronizers remain | Verify all serializers/admin/callers before contracting |
| Queue ordering and login merge | SF-11 | Preserve current explicit routes and dual fields | DB/caller/concurrency migration evidence |
| FileField audio/CloudFront and offline endpoints | SF-13/SF-14/SF-19 | Preserve protected legacy behavior and disable gates | Object/provider/client cutover evidence |
| `conf.settings` / `conf.settings.local` aliases | SF-02 | Keep existing deprecated development shims | Developer/deployment caller audit |
| Liveness `service` response | SF-01 | Current response remains `90Nutmegs`; stale test corrected and zero-I/O asserted | SF-01 approved; runtime contract unchanged |

## Canonical Owners Established

No new owner is established or approved by SF-00. These are observed owners/candidates to preserve and verify.

| Concept | Canonical Owner | Concern | Evidence |
|---|---|---|---|
| User identity | Existing `users.ClerkUser` + `apps.accounts.identity` verified mapping | SF-05 | Unique external ID, real signed-token/local privilege tests; review pending |
| Staff roles and audit | Existing local staff/superuser flags, Django permissions and `admin.LogEntry` | SF-05 | Active-staff boundaries and atomic mutation/audit tests; review pending |
| Access decisions | `memberships.policies.AccessPolicy` | SF-08 | Structured decisions, policy callers/tests; facade remains |
| Podcast content | `podcasts.Podcast/Season/Episode` | SF-06 | Services, selectors, migrations 0002/0003 |
| Media identity/provider boundary | `MediaAsset/Location/Variant`, provider contracts | SF-13/SF-14 | DB constraints + primitive tests; API integration missing |
| Playback | Existing `podcasts.PlayBack` | SF-10 | Current writes/reads and tests |
| Queue | Existing `queue.Queue/QueueItem` | SF-11 | Current routes, login receiver and tests; duplicate ordering unresolved |
| Playlist/free follow | Existing media PlayList + analytics subscriber M2M | SF-12 | Profile routes; split ownership unresolved |
| Comments | `comments.Comment` for routed comments | SF-16 | Create view/serializer; forum duplicate remains |
| Discovery | Podcast selectors currently serve Explore | SF-18 | `queries.py` caller trace; other generations unresolved |

## Infrastructure Decisions

| Decision | Concern / ADR | Status | Notes |
|---|---|---|---|
| Preserve modular monolith and provider-neutral owners | SF-00 design note / master A.5–A.6 | Existing authority observed | No new ADR or architecture approval |
| Cloudflare via pycflare for R2/Images/Stream | SF-13/SF-14/master | Existing code/required production configuration | Primitives exist; actual routed transfer/cutover incomplete or unknown |
| Documentation-only baseline with isolated checks | SF-00 | Implemented within scope | No deployment/provider/persistent-data mutations |
| Explicit proxy/HSTS activation and central redacted console logging | SF-02 | Approved by user | Environment-owned configuration; no deployed topology/secret-manager decision |

## Hosting / Deployment Status

WSGI/ASGI/Celery entrypoints exist and default to production. No tracked executable deployment topology, Docker/Compose/Procfile/IaC, release promotion or rollback runbook found. SF-03 now supplies bounded Gunicorn/Celery role commands and rollout/rollback guidance. Hosting provider/regions/deployed replicas and operational capacity remain unknown (SF-21/SF-25). No deployment performed.

## Media Storage / CDN Status

Production requires private default R2 FileField storage, separate public/private buckets, Images/Stream configuration and cutover confirmation. Cloudflare access is wrapped by pycflare adapters. Direct upload/finalization/delivery services have tests but no non-test runtime API caller found. Legacy APIs/tasks use FileFields, boto3/S3 and CloudFront; thumbnail/metadata helpers still require local `.path`. Provider object inventory, edge/IAM policies and completed cutover are unverified (SF-13/SF-14/SF-23).

## Database / Cache / Broker Status

Production PostgreSQL is required; connection age defaults to 60 seconds with health checks. Redis cache and broker URLs are separately configurable; Celery results use the database. No pool/connection budget, Redis cap, TLS/private network configuration or live deployment evidence establishes operational readiness. Tests use SQLite/locmem/eager Celery; PostgreSQL SQL/locks and broker durability remain unverified (SF-22/SF-24).

## Queue / Worker Capacity Status

SF-03 preserves six task identities and adds three registered maintenance wrappers, explicit celery/media/bulk queues, prefetch/concurrency/task-time bounds and separate process commands. Queue consumer cutover, legacy draining, single beat and staging maintenance review are documented in docs/runtime.md. Audio retry/charging/overwrite behavior and OS/subprocess/disk budgets remain SF-15/SF-19/SF-21. No real provider/broker work or deployment performed; process probes used isolated memory transport and idle workers.

## Backup / Restore / DR Status

No tracked backup schedules/scripts, tested restore evidence, RPO/RTO or DR runbook found. Actual deployed backups are unknown; source absence does not establish absence in production. No backup/restore action performed (SF-26).

## Observability / Alerts Status

Liveness/readiness, normal logs, DB task results and four transcription Prometheus metrics exist. Readiness probes SQL/cache with sanitized failures, not broker/worker/provider health. No scrape setup/route, alerts, tracing, structured logging policy, dashboards, SLO/capacity evidence or operations runbooks found. SF-01 corrected the stale liveness assertion. SF-02 configures redacted console/exception logging, without deployment collectors or alerts (SF-27). SF-05 adds metadata-only staff mutation records to the existing admin audit log and sanitized identity-failure events; no deployed alert/retention infrastructure is claimed.

## IaC / CI/CD Status

Baseline `.github/workflows/backend.yml` failures remain historical below. SF-01 corrects scoped formatting and suite failures. SF-02 expands existing lint/format scopes and synthetic production environment; all those checks pass locally. SF-03 resolves the inherited advisory matches and audits both web/worker profiles; schema warnings remain with feature owners. SF-04/SF-05 expand compatibility/security gates; 381 tests pass at 65%. Latest worker audit is inconclusive because PyPI returns 503, while the unchanged worker lock passed SF-04. No infrastructure/deployment pipeline was added (SF-25).

## Security / Privacy Risks

Severity is a baseline priority estimate, not a validated exploit rating.

| Risk | Severity | Concern | Owner | Exit Condition |
|---|---|---|---|---|
| Baseline 17 dependency advisory matches resolved by SF-03; VCS pycflare remains outside scanner coverage | Review pending | SF-03 / SF-05 | Dependency/runtime and identity reviewers | Web and worker audits pass after PyJWT/urllib3 upgrades; auth regressions pass; review immutable Git dependency separately |
| Generic comment creation lacks target policy/publication allowlist and parent-target validation | High review priority | SF-16 / SF-08 | Community/access owners | Negative authorization/moderation characterization and explicit enforcement |
| Compatibility access Boolean cache/invalidation failures may differ from uncached structured policy | Medium | SF-08 | Access owner | Trace cached callers, revocation/expiry and failure tests |
| Anonymous playback IP and cookie history; analytics/license retention not established | Medium | SF-10 / SF-17 / SF-19 | Domain/privacy reviewers | Stable anonymous identity and documented retention/access rules |
| Legacy card/offline key-bearing data and direct AWS paths remain | High review priority | SF-09 / SF-19 | Billing/offline reviewers | Data/caller review; preserve default-disabled offline and redaction controls |
| Proxy/network trust and deployment rotation posture remain unverified | Unassessed | SF-02 / SF-24 | Settings/infrastructure owners | SF-02 supplies explicit proxy/HSTS switches and rotation/redaction tests; verify deployment/least privilege before activation |
| Limited current/history credential-pattern scan found no matches; deployed secrets/rotation/IAM remain unverified | Unassessed | SF-02 / SF-24 | Settings/secrets and deployment owners | 553 current files + 573 selected blobs / four commits checked; examples synthetic. Not an exhaustive secret audit; review actual deployment inventory in SF-24 |

## Cost / Capacity Risks

| Risk | Concern | Measurement | Threshold / Exit Condition |
|---|---|---|---|
| Duplicate audio/transcription retries and unlocked quota charging | SF-15 | Attempts/provider bills/quota consistency; unmeasured | Idempotent attempts and measured quotas |
| Audio variants/HLS/preview copies, temporary FFmpeg disk/CPU | SF-13/SF-21/SF-27 | Bytes/episode, CPU, peak disk, queue age; unmeasured | Lifecycle and workload budgets established |
| AWS/KMS + Cloudflare coexistence and provider egress | SF-19/SF-23/SF-27 | Provider/object/bandwidth accounting; no bill available | Verified cutover, retention and cost attribution |
| Recommendation N+1/full-window scoring and all-episode trending lists | SF-18 | Query count, memory/time on representative data; unmeasured | Bounded execution and workload acceptance |
| Analytics/task results/licenses/artifacts growth | SF-17/SF-18/SF-19/SF-27 | Retention/storage trends; unmeasured | Explicit retention, capacity and alert thresholds |
| Unbounded worker/DB/cache connection assumptions | SF-21/SF-22 | Concurrency × connections and queue saturation; unknown | Measured pool/queue budgets and backpressure |

## Tests / Quality Gates

SF-00 rows refer to unchanged application commit `e24ff2e`, 2026-10-11. SF-01/SF-02 rows refer to their working-tree patches on that commit. Exact expanded CI commands, audit IDs and reproduction are in [baseline-validation.md](docs/baseline-validation.md).

| Concern | Command / Suite | Result | Date/Commit | Notes |
|---|---|---|---|---|
| SF-00 | `uv sync --locked --extra dev`; `uv run --locked python -m pip check` | PASS | 2026-10-11 / e24ff2e | Python 3.14.8; writable /tmp caches |
| SF-00 | `uv run --locked python -m compileall -q app` | PASS | same | All source compiles |
| SF-00 | Workflow `ruff format --check` scope | FAIL | same | One existing podcast API test formatting difference |
| SF-00 | Workflow `ruff check` scope; six-file `mypy` scope | PASS | same | No fixes performed |
| SF-00 | `manage.py check --settings=conf.settings.test` | PASS | same | No issues |
| SF-00 | `manage.py check --deploy --settings=conf.settings.production` | PASS with warnings | same | Synthetic CI env; 45 schema warnings |
| SF-00 | `manage.py makemigrations --check --dry-run --settings=conf.settings.test`; `showmigrations --plan` | PASS | same | No drift; fresh graph resolves |
| SF-00 | `manage.py spectacular --settings=conf.settings.test` | PASS with warnings | same | 84 warnings, 45 unique; zero errors |
| SF-00 | Locked export + `pip-audit --no-deps --disable-pip` | FAIL | same | 17 advisories / 2 packages; pycflare skipped |
| SF-00 | `coverage run app/manage.py test --settings=conf.settings.test --verbosity=1` | FAIL | same | 275 run; 274 pass; one liveness-name assertion fails |
| SF-00 | `coverage report --fail-under=50`; coverage XML | PASS | same | 61%; does not negate suite failure |
| SF-00 | Django/Celery registry probes | PASS inventory / FAIL schedule consistency | same | Six tasks; four unregistered beat targets |
| SF-00 | Master checksum vs committed `.sha256` | FAIL | same | Actual e4cf7f… vs expected f17c7b…; master equals HEAD bytes |
| SF-00 | PostgreSQL/real worker/provider/load/restore/E2E validation | NOT RUN | same | No applicable deployed environment; limits explicitly recorded |
| SF-00 | `git diff --check`; documentation link/fence/whitespace and tracked-byte preservation checks | PASS | same | Six documentation files only; all 538 other tracked files and all 45 later concern rows unchanged; required sections preserved |
| SF-01 | Complete coverage suite; workflow format/lint/type/check/compile/drift/schema/coverage | PASS | 2026-10-11 / e24ff2e + SF-01 patch | 298 tests, 62%; schema warnings remain; no dependency change/audit rerun |
| SF-02 | `test conf.test_configuration conf.test_logging --settings=conf.settings.test` | PASS | 2026-10-11 / e24ff2e + SF-02 patch | 33 tests, including actual Celery logger setup, redaction, rotation and malformed startup inputs |
| SF-02 | Complete coverage suite; workflow format/lint/type/check/compile/drift/schema/coverage | PASS | same | 331 tests, 63%; 45 unique schema warnings, zero schema errors; no dependency change/audit rerun |
| SF-02 | `check --settings=conf.settings.development`; dotenv ignore rules; pre-existing-file hash preservation | PASS | same | Local boot; `.env.*` ignored except tracked example; SF-01 and approved snapshots preserved |
| SF-02 | Scoped current/history credential-pattern scan; example inspection; documentation links/tables; `git diff --check` | PASS | same | No credential-pattern findings; synthetic examples only; limits in packet above |
| SF-03 | Full suite and workflow gates; development check; offline lock check | PASS | 2026-10-12 / e24ff2e + SF-03 patch | 343 tests, 64%; 45-file Ruff scope; schema warnings remain |
| SF-03 | Web and combined-worker locked profile audits; actual optional dependency compatibility | PASS | same | No known vulnerabilities; VCS pycflare skipped; writable cache required in managed workspace |
| SF-04 | Route/registry/model lookup tests, complete suite, workflow and both audits | PASS | 2026-10-12 / e24ff2e + SF-04 patch | 350 tests, 64%; exact 174-route capture plus reverse aliases preserved |
| SF-05 | Identity, staff/audit, privacy, login, endpoint contracts; complete suite and local workflow checks | PASS | 2026-10-13 / e24ff2e + SF-05 patch | 381 tests, 65%; 108-file lint/format, six-file mypy, startup, drift and schema pass |
| SF-05 | Current locked web audit | PASS | same | No known vulnerabilities; immutable VCS dependency skipped |
| SF-05 | Current locked worker audit retries | INCONCLUSIVE | same | PyPI timeout then 503; same lock passed SF-04; retry before release |

| SF-06 | Focused content/taxonomy/sports/API/migration suite; complete coverage suite | PASS | 2026-10-14 / 7ba8eba + local SF-06 patch | 83 focused; 407 full, 66% coverage; 26 additional tests |
| SF-06 | All 16 workflow commands, including both locked dependency audits | PASS | same | 125-file formatting, scoped lint, six-file mypy, startup, drift, schema and coverage; VCS dependency skipped by audit |
| SF-06 | Final diff whitespace, 46-row dependency recomputation, specification preservation and changed-model lint | PASS | same | No downstream eligible concerns; master remains unchanged; exact approved remote SHA verified |

## ADRs

| ADR | Concern | Status | Summary |
|---|---|---|---|
| No new ADR | SF-00 | Not applicable | Current-state design note preserves master authority and existing implementation; no architecture decision requiring adoption made |

## Known Risks

| Finding / evidence | Later owner | Required followup |
|---|---|---|
| Master checksum mismatch predates SF-00; `.sha256` references an obsolete package path. Actual file hash `e4cf7f962f62c9f9e97bf60440019b9cf3c0302e46e2c3c433541c561fd39eeb`; expected `f17c7bb0bf30a0ffeb9db57ed30a2fcd9a96ada162e110bb82f80ed4f1f0d62c` | Human reviewer / source authority | Establish original-package provenance before acceptance; neither master nor checksum changed |
| Baseline liveness branding assertion and one scoped formatting failure | SF-01 | Corrected and validated in SF-01; approved by user |
| `memberships/services.py` uses absent `granted_by_purchase`/`Plan.slug`; no runtime callers found | SF-07/SF-09 | Characterize/reconcile fulfillment helpers before calling them operational |
| Profile playlist queryset selects absent `image` relation and applies user filter to anonymous reads | SF-12 | Reproduce routed behavior with ownership/privacy tests before repair |
| Queue duplicate ordering/active-owner races; playback anonymous/new-row concurrency gaps | SF-10/SF-11 | PostgreSQL concurrency and compatibility characterization, then scoped constraints/services |
| UUID/text join and nullable-user aggregation in PostgreSQL affinity task | SF-18 | Run representative PostgreSQL test, reconcile schema/query; no speculative rewrite |
| Multiple recommenders, N+1 scoring, unbounded queue expansion/trending memory | SF-11/SF-18 | Trace actual callers and measure; converge only after compatibility evidence |
| Local thumbnail `.path` and metadata probes conflict with remote FileFields; canonical upload/delivery APIs unconnected | SF-13/SF-14 | Provider/caller/object reconciliation and direct-transfer integration |
| R2 finalization can leave pending reservation after external promotion failure | SF-14 | Interrupted-attempt recovery and idempotency verification |
| Audio retry/storage overwrites, repeated transcription billing, quota races and processed-on-partial-failure state | SF-15 | Explicit attempt/status/idempotency and charging tests |
| SF-03 fixes beat targets/routes; inherited cadence labels/timezones still require deployment review | SF-19/SF-21 | Inspect maintenance effects/cadence and migrate any persisted beat state deliberately |
| Match receiver registration, Region insert recursion and sports code collision retry | SF-06 | Fixed; creation/raw/replay/rollback/structured relationship tests pass |
| Old Matches may lack Events; existing Match team edits do not reconcile possession-team references; partial updates expect both teams | SF-35/SF-40 | Inspect existing/imported data and define score/team transition semantics; do not fabricate historical score state |
| Existing Player receiver creates Fitness on raw saves and replaces a supplied zero code | SF-35 | Characterize player ingestion/fixtures before changing that lifecycle; existing IDs/relations unchanged here |
| Raw/bulk content writes and concurrent admin graph edits can bypass dashboard freshness checks | SF-20 / operations | Use explicit services, content drift audit and PostgreSQL concurrency review before production cutover |
| Dormant event framework and post-commit publication without durable outbox | SF-17 | Explicit event ownership and retry-safe publication |
| Promotion byte upload synchronous; callback updates have no row lock/version ordering | SF-18 | Provider/update ordering and throughput characterization |
| Schema warnings remain; SF-04 removed all live custom loaders | Feature owners / SF-20 | Resolve serializer/schema warnings within each feature contract; 45 unique warnings, zero errors |
| No deployed inventory, connection budgets, backup/restore proof or cost evidence | SF-21–SF-28 | Obtain measured operational evidence in authorized concerns |
| SF-05 fixes real session-login queue handoff; anonymous queue writes and bearer merge/concurrency remain | SF-11 | Characterize anonymous mutation/merge policy and implement canonical queue invariants in SF-11 |
| Follow POST toggles M2M then raises missing item_id; followed-library GET calls absent get_user_subscriptions | SF-12 | Repair retry-safe API representation and canonical library selector with regression tests |
| Partial progress PATCH omits defaulted is_completed and raises KeyError | SF-10 | Define partial update contract and validate omitted fields |
| Dashboard audio DELETE/PATCH share a path; DELETE callback shadows PATCH | SF-04/SF-14 | Consolidate method routing with client/permission regression tests |
| Managed transcription uses literal OpenAI API-key text and drops object response fields through normalization precedence | SF-15 | Use configured credential/client and characterize successful SDK response forms before enabling provider processing |
| Existing orphan-package GC swallows storage-delete failures then deletes the DB row | SF-19 | Staging review before schedule activation; define retry/retention/data reconciliation semantics |
| Task hard limits do not establish FFmpeg descendant cleanup or temporary disk bounds; dormant ML matrix module trains at import | SF-15/SF-18/SF-21 | Bound subprocess/disk lifecycle in media owner; remove/converge dormant training only after caller/data review |
| Plan create response tries to iterate a related manager as ListField data | SF-07 | Repair create/display serializer boundary; SF-05 audit transaction now rolls back failed responses |
| SF-05 worker audit encountered upstream PyPI timeout/503; lock unchanged | Resolved verification in SF-06 | Both locked web/worker audits now PASS (2026-10-14); preserve historical result |
| Existing SESSION_SAVE_EVERY_REQUEST causes session DB writes when health probes send cookies | SF-21 / SF-27 | Operational probes should omit cookies; evaluate middleware isolation in deployment hardening |
| Per-request Clerk/JWKS verification and staff audit growth not measured in deployment | SF-24 / SF-27 | Verify provider revocation, pre-auth abuse controls, network budget and audit retention/capacity |

## Review / Approval Log

> Only a human/reviewer may add an `APPROVED` entry.

| Concern | Decision | Reviewer | Date/Commit | Review Notes |
|---|---|---|---|---|
| SF-00 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-11 / baseline e24ff2e | Inventory complete; failures and provenance discrepancy recorded. No approval granted. |
| SF-00 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-11 / baseline e24ff2e + SF-00 working-tree packet | Review note: "I have reviewed SF-00 and approve it." User also requested readiness recomputation and implementation of all currently READY concerns (SF-01, SF-02). |
| SF-01 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-11 / e24ff2e + SF-01 patch | 298 tests pass; known unsupported/defective journeys documented; no approval granted. |
| SF-02 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-11 / e24ff2e + SF-02 patch | 331 tests pass; security/configuration, logging, rotation and compatibility checks documented; no approval granted. |
| SF-01 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-11 / e24ff2e + reviewed working-tree patch | Review note: "I have reviewed SF-01 and SF-02 and approve it." User requests readiness recomputation and implementation of the eligible set SF-03, SF-04, SF-05. |
| SF-02 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-11 / e24ff2e + reviewed working-tree patch | Review note: "I have reviewed SF-01 and SF-02 and approve it." User requests readiness recomputation and implementation of the eligible set SF-03, SF-04, SF-05. |
| SF-03 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-12 / e24ff2e + SF-03 patch | Runtime/dependency work complete and validated; no approval granted. |
| SF-04 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-12 / e24ff2e + SF-04 patch | Framework removal and compatibility checks complete; no approval granted. |
| SF-05 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-13 / e24ff2e + SF-05 patch | Identity/staff/privacy/login implementation complete; 381 tests pass. Current worker audit inconclusive due PyPI 503; unchanged lock passed SF-04. No approval granted. |
| SF-03 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-13 / reviewed SF-00–SF-05 working tree | Review note: "I have reviewed SF-03, SF-04, and SF-05 and approve it." User authorizes implementation of all newly READY concerns and committing/publishing approved changes to GitHub for testing. |
| SF-04 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-13 / reviewed SF-00–SF-05 working tree | Review note: "I have reviewed SF-03, SF-04, and SF-05 and approve it." User authorizes implementation of all newly READY concerns and committing/publishing approved changes to GitHub for testing. |
| SF-05 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-13 / reviewed SF-00–SF-05 working tree | Review note: "I have reviewed SF-03, SF-04, and SF-05 and approve it." User authorizes implementation of all newly READY concerns and committing/publishing approved changes to GitHub for testing. |
| SF-06 | `READY_FOR_REVIEW` | Human review pending; prepared by Codex | 2026-10-14 / approved 7ba8eba + separate local SF-06 patch | 407 tests, all workflow gates and both audits PASS; no approval granted. |

| SF-06 | `APPROVED` | User, explicitly in this chat; recorded by Codex | 2026-10-14 / reviewed SF-06 working-tree patch | Review note: "I have reviewed SF-06 and approve it." User authorizes implementation of all newly READY concerns and publishing approved uncommitted changes to GitHub for testing. |

## Next Actions

1. Publish the human-approved SF-00–SF-06 code on `codex/approved-sf00-sf06` for user testing; preserve the earlier SF-00–SF-05 checkpoint.
2. All 46 dependency rows recomputed: newly READY set is SF-07, SF-10, SF-16 and SF-17. User explicitly requested all; execute sequentially, one active concern at a time, each ending READY_FOR_REVIEW without self-approval. Keep new implementation separate from the approved GitHub checkpoint.
3. SF-08/SF-11 and all other dependents remain gated until their prerequisites receive human approval. Do not use READY_FOR_REVIEW to unlock them.
