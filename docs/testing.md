# Characterization and regression testing

Use Python 3.14 and the unchanged `uv.lock`. Select `conf.settings.test` explicitly; it uses an in-memory SQLite database, locmem cache, eager Celery and disabled/fake external providers. No production credentials are needed. The [SF-00 baseline](baseline-validation.md) remains a historical record of the original 275-test run and its failures. Current concern status and results live in [the execution ledger](../SANFOOTBALL_IMPLEMENTATION_STATUS.md).

```bash
uv sync --locked --extra dev
uv run --locked python app/manage.py check --settings=conf.settings.test
uv run --locked python app/manage.py test --settings=conf.settings.test --verbosity=1
uv run --locked coverage run app/manage.py test --settings=conf.settings.test --verbosity=1
uv run --locked coverage report --fail-under=50
uv run --locked python app/manage.py makemigrations --check --dry-run --settings=conf.settings.test
```

The custom `SourceRootDiscoverRunner` discovers below `app/` even when invoked from the repository root. Never interpret a zero-test run as a passing baseline. Use the workflow's scoped formatting/lint/type checks as well as checks on newly added files. On a managed workspace with a read-only home, set `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `COVERAGE_FILE`, `RUFF_CACHE_DIR` and `MYPY_CACHE_DIR` to writable temporary paths as described in the baseline report.

## SF-01 design and owner map

The existing AccessPolicy, media capabilities, billing models, Queue, PlayBack and podcast migrations remain the owners. Add executable coverage at missing HTTP and transaction boundaries; preserve existing behavior tests instead of duplicating them. Do not implement absent target features or make security/correctness defects part of the compatibility contract. No domain code, settings, dependency or migration change belongs to SF-01.

SF-01 reads its mapped master sections and additionally Part I §16 because §35.5 explicitly requires that access matrix. Existing `AccessPolicyMatrixTests` cover the matrix's anonymous/free/tiered/trial/past-due/canceled/expired/entitled/revoked/staff/early-access/public/preview/download/transcript cases. The canonical media tests additionally bind decisions to principal, action, exact variant/location and expiry. This is local regression evidence, not production-provider validation.

| Behavior | Executable evidence | Boundary / limitation |
|---|---|---|
| Access and commercial lifetime | `apps.memberships.tests` | Uses real ORM/policy; canonical Price/subscription redesign is later work. |
| Protected streaming, preview, HLS scope and expiry | `api.rest.web.apps.media.streaming.tests` | Provider signing mocked; no unsigned/full capability on denial. |
| Download distinct from stream; disabled offline pipeline | Membership tests, `api.rest.web.apps.media.offline.tests`, `apps.media.offline.tests` | Custom offline feature disabled by default; no live KMS/storage integration. |
| Billing replay-safe transitions/refunds, source ledger, cancellation | `apps.billing.tests` | No payment-provider webhook endpoint exists to characterize; SF-09 owns it. |
| Playback identity, bounds, completion and history | `apps.posts.podcasts.tests` and listener journeys | Anonymous IP identity and first-write races remain SF-10 correction targets. |
| Queue add/deduplication/order/publication/receiver merge | `apps.queue.tests` and API contracts | Receiver-level merge is distinct from actual authentication/session rotation. Concurrent ordering needs SF-11's design and PostgreSQL evidence. |
| Publication, compatibility and data migrations | Public/dashboard podcast tests; `test_publication_migration`, `test_content_migration`, `test_audit_podcast_content_command` | Historical rows, duplicates and invalid graphs already covered; no new migration requires another fixture generation. |
| Literal routes and HTTP ownership/method behavior | `conf.test_api_contracts` | Helps distinguish routing-refactor regressions from documented defective paths. |
| Supported listener journeys across routes and ORM | `conf.test_listener_journeys` | Real selectors/policy; provider boundary faked. Unsupported end-to-end paths are documented separately. |
| Transaction → audio task publication | `apps.media.audio.test_dispatch` | Real commits/savepoints/rollbacks; mock only Celery dispatch; does not establish durable outbox/redelivery. |
| Liveness | `conf.test_health` | Existing `90Nutmegs` response, zero DB queries and no cache calls. |

## Known defects are intentional future correction targets

The ledger owns the full risk list and assigned concerns. The following are deliberately not asserted as required behavior:

- Queue `position`/`order` duplication, lack of active-owner/position uniqueness and concurrent reorder semantics (SF-11). The full target queue matrix cannot be declared complete against the current implementation.
- Missing payment-provider checkout/webhook/idempotency lifecycle (SF-09). Existing transaction tests are not substitutes for webhook tests.
- Generic comment target authorization, playlist query/model mismatch, text/UUID recommendation SQL and dormant commercial helpers (SF-07/SF-09/SF-12/SF-16/SF-18).
- Marking audio processed after transcription failure (SF-15). The old test's assertion requiring that defective state was removed; failure logging and temporary-file cleanup remain tested. Successful processing retains its existing state assertion.
- Unconnected canonical upload/delivery primitives, direct-provider production flows and full client journeys (SF-13/SF-14 and later feature concerns).

Do not silently add `expectedFailure`, broad skips or mocks around these domain defects to obtain a green suite. Reproduce and record a defect, then change its owning concern with explicit regression tests. Supported characterization tests should stay green; the ledger must distinguish those passes from absent target functionality.

SF-01's temporary diagnostics additionally reproduced these existing defects on disposable databases; they are not retained as passing compatibility tests:

| Reproduction | Observed result | Correction owner |
|---|---|---|
| Create a queue keyed by an anonymous client's session, then use Django login / `client.force_login(user)` | Login rotates the session key before `user_logged_in`; the receiver looks up the new key, leaving the old queue unmerged | SF-05/SF-11 |
| Anonymous `POST /api/rest/web/apps/queue/add/` or `PUT …/queue/clear/` | HTTP 401 from inherited permissions despite anonymous model support; anonymous GET isolation does work | SF-11 |
| Authenticated `POST /api/rest/web/apps/profile/subscribe/` with valid `item_id` and `app_label=podcasts.Podcast` | Follow M2M changes, then response serialization raises `KeyError('item_id')`; retry can toggle it back | SF-12 |
| Authenticated `GET /api/rest/web/apps/profile/subscriptions/podcast/` | Missing `Podcast.objects.get_user_subscriptions` raises AttributeError | SF-12 |
| Authenticated `PATCH /api/rest/web/apps/podcast/episode/<slug>/update-playback` with only `seconds` | Partial serializer suppresses defaults; update indexes absent `is_completed` and raises KeyError. Both fields work | SF-10 |
| Resolve dashboard `…/podcasts/episodes/<id>/audio/<audio_id>/` | First matching route maps DELETE only; separate PATCH action is shadowed at the same path | SF-04/SF-14 |

The listener follow test intentionally exercises the current domain method and then real metadata/stream routes; it does not claim the follow HTTP endpoint works. The progress journey sends both supported fields. The suite therefore preserves useful behavior while making the unimplemented acceptance paths explicit.

## Environment limits and reviewer checks

SQLite cannot establish PostgreSQL row-lock races or SQL compatibility. Eager/local task tests cannot establish real broker retry, ordering, loss or worker isolation. No frontend or deployed service is supplied; multi-device, live storage/identity/payment-provider and load/restore scenarios remain later gates.

Review added tests for real route resolution, actual ownership/policy queries and side-effect isolation. Re-run the complete suite plus migration drift and workflow lint/format/type gates. Check the ledger for actual results, failures and the precise changed-file list; do not infer later concern approval from test success.

## Identity foundation coverage

SF-05 adds signed JWT verification, canonical identity mapping, dashboard access
and audit rollback, privacy allowlists and real Django login-session rotation
coverage. The earlier SF-01 statements remain historical descriptions of its
test scope. See [identity and authorization](identity-and-authorization.md) for
focused commands, compatibility restrictions and staging limitations.
