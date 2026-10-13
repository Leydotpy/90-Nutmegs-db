# SF-00 baseline validation

Executed 2026-10-11 against application commit `e24ff2e9c9ae7ecb563215f1cfc4f1b6e6687c6e`. Only documentation changed. This evidence snapshot is not a second execution ledger. Findings/owners and review state are in [SANFOOTBALL_IMPLEMENTATION_STATUS.md](../SANFOOTBALL_IMPLEMENTATION_STATUS.md).

## Environment and isolation

- Python 3.14.8; default + dev dependencies installed from unchanged `uv.lock` (117 distributions; 187 lock entries include optional extras). Host Python 3.12 is not a valid baseline for this project’s syntax.
- `uv sync --locked --extra dev` — PASS. Initial cache access failed because the managed home is read-only; cache/runtime locations below resolved it. Initial download without network permission failed; the permitted package-manager network path completed installation. Neither issue required repository changes.
- Test settings use disposable SQLite, in-process cache and eager Celery. Production smoke uses the workflow’s synthetic values and a temporary generated signing key; no real deployment credentials or services were used.
- Commands were taken from `.github/workflows/backend.yml`. All independent gates were run even after failure, so coverage/schema evidence exists although a normal CI job would stop earlier.
- Temporary logs, schema, coverage data/XML, audit cache and probe scripts are under `/tmp/sf00-checks`; that directory is disposable. The durable commands/results are recorded below. No generated artifact is required to interpret this report.

For the same managed workspace, use writable caches (ordinary local development can use its default cache paths):

```bash
export UV_CACHE_DIR=/tmp/sf00-uv-cache
export UV_PYTHON_INSTALL_DIR=/tmp/sf00-python
export COVERAGE_FILE=/tmp/sf00-checks/.coverage
export MYPY_CACHE_DIR=/tmp/sf00-checks/mypy-cache
export RUFF_CACHE_DIR=/tmp/sf00-checks/ruff-cache
mkdir -p /tmp/sf00-checks
uv sync --locked --extra dev
```

## Existing CI gates actually executed

| Command | Result | Evidence / limits |
|---|---|---|
| `uv run --locked python -m pip check` | PASS (exit 0) | No broken requirements found. |
| `uv run --locked python -m compileall -q app` | PASS (exit 0) | All app source compiled under Python 3.14.8. |
| `uv run --locked ruff format --check app/apps/media/canonical.py app/apps/media/migrations/0002_mediaasset_medialocation_mediavariant.py app/apps/media/providers app/apps/media/upload_intents.py app/apps/media/upload_finalization.py app/apps/media/delivery_service.py app/apps/media/test_upload_intents.py app/apps/media/test_upload_finalization.py app/apps/media/test_delivery_service.py app/apps/media/tests.py app/apps/memberships/policies.py app/apps/memberships/tests.py app/apps/posts/podcasts/migrations/0002_episode_publication_access.py app/apps/posts/podcasts/services.py app/apps/posts/podcasts/test_publication_migration.py app/apps/posts/podcasts/tests.py app/apps/queue/tests.py app/apps/billing/tests.py app/api/rest/web/apps/media/offline/tests.py app/api/rest/web/apps/media/streaming/tests.py app/api/rest/web/apps/podcasts/tests.py app/api/rest/dashboard/apps/podcasts/tests.py app/conf/settings/production.py app/conf/tests.py` | FAIL (exit 1) | 1 of 28 files needs formatting: app/api/rest/web/apps/podcasts/tests.py:295 (multiline set comprehension). Existing source left unchanged. |
| `uv run --locked ruff check app/apps/media/canonical.py app/apps/media/migrations/0002_mediaasset_medialocation_mediavariant.py app/apps/media/providers app/apps/media/upload_intents.py app/apps/media/upload_finalization.py app/apps/media/delivery_service.py app/apps/media/test_upload_intents.py app/apps/media/test_upload_finalization.py app/apps/media/test_delivery_service.py app/apps/media/tests.py app/apps/memberships/policies.py app/apps/memberships/tests.py app/apps/posts/podcasts/migrations/0002_episode_publication_access.py app/apps/posts/podcasts/services.py app/apps/posts/podcasts/test_publication_migration.py app/apps/posts/podcasts/tests.py app/apps/queue/tests.py app/apps/billing/tests.py app/api/rest/web/apps/media/offline/serializers.py app/api/rest/web/apps/media/offline/tests.py app/api/rest/web/apps/media/streaming/tests.py app/api/rest/web/apps/podcasts/tests.py app/api/rest/dashboard/apps/podcasts/tests.py app/conf/settings/production.py app/conf/tests.py` | PASS (exit 0) | All checks passed for the existing workflow scope. |
| `uv run --locked mypy app/apps/media/providers/contracts.py app/apps/media/providers/config.py app/apps/media/providers/cloudflare.py app/apps/media/upload_intents.py app/apps/media/upload_finalization.py app/apps/media/delivery_service.py` | PASS (exit 0) | No issues in 6 source files. |
| `uv run --locked python app/manage.py check --settings=conf.settings.test` | PASS (exit 0) | No issues (0 silenced). |
| `uv run --locked python app/manage.py check --deploy --settings=conf.settings.production` | PASS (exit 0) | Exit 0; 45 schema warnings. Synthetic CI configuration; no production connectivity/cutover verification. |
| `uv run --locked python app/manage.py makemigrations --check --dry-run --settings=conf.settings.test` | PASS (exit 0) | No changes detected. |
| `uv run --locked python app/manage.py spectacular --settings=conf.settings.test --file /tmp/sf00-checks/openapi.yaml` | PASS (exit 0) | 84 warnings (45 unique), 0 errors. |
| `uv run --locked coverage run app/manage.py test --settings=conf.settings.test --verbosity=1` | FAIL (exit 1) | 275 tests ran in 28.132s: 274 passed, 1 failed; no skips reported. Health liveness service-name assertion is stale relative to current response. |
| `uv run --locked coverage report --fail-under=50` | PASS (exit 0) | 61% combined coverage; passes the existing 50% threshold despite the failed test. |
| `uv run --locked coverage xml -o /tmp/sf00-checks/coverage.xml` | PASS (exit 0) | Coverage artifact generated; does not make the test suite green. |
| `uv export --locked --no-dev --no-emit-project --no-editable --no-hashes --quiet --output-file /tmp/sf00-checks/audit-requirements.txt` | PASS | Locked default production requirements exported. |
| `uv run --locked pip-audit --requirement /tmp/sf00-checks/audit-requirements.txt --no-deps --disable-pip --progress-spinner off --cache-dir /tmp/sf00-checks/audit-cache` | FAIL (exit 1) | 17 advisories in 2 packages; Git-sourced pycflare skipped. |
| `uv run --locked python app/manage.py showmigrations --plan --settings=conf.settings.test` | PASS | Migration graph resolves; all rows unapplied in the fresh in-memory database. |

The production smoke command requires exactly the synthetic `env` block and signing-key generation in the workflow; do not substitute production credentials. Coverage XML location and cache flags are safe workspace adaptations of the workflow commands.

## Failure and warning details

1. **Test mismatch:** `conf.test_health.HealthEndpointTests.test_liveness_is_dependency_free`, `app/conf/test_health.py:12`, expects `{"status":"ok","service":"sanfootball"}`. `app/conf/health.py:17` returns `{"status":"ok","service":"90Nutmegs"}`. SF-01 must characterize the intended contract under the renamed product. SF-00 leaves both unchanged.
2. **Formatting:** `app/api/rest/web/apps/podcasts/tests.py:295` is the sole scoped Ruff formatting failure; lint still passes. SF-01 owns the test maintenance followup.
3. **Dependency audit:** advisory matches are scanner results, not a demonstrated application exploit. PyJWT 2.13.0 has 14 advisories and urllib3 2.7.0 has 3. SF-03 must triage/update through lock and compatibility review, with SF-05 assessing authentication relevance. The audit does not cover the pinned Git source `pycflare` or uninstalled optional worker dependencies.
4. **Schema warnings:** type inference falls back to strings, CommentCreate component identity collides, and several operation IDs collide. The schema test accepts zero errors; warnings remain an SF-04/API-owner review item.

Dependency audit output (2026-10-11):

```text
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Found 17 known vulnerabilities in 2 packages
Name    Version ID              Fix Versions
------- ------- --------------- ------------
pyjwt   2.13.0  PYSEC-2026-4145 2.14.0
pyjwt   2.13.0  PYSEC-2026-4146
pyjwt   2.13.0  PYSEC-2026-4149 2.14.0
pyjwt   2.13.0  PYSEC-2026-4152 2.14.0
pyjwt   2.13.0  PYSEC-2026-4144 2.14.0
pyjwt   2.13.0  PYSEC-2026-4143 2.14.0
pyjwt   2.13.0  PYSEC-2026-4148 2.14.0
pyjwt   2.13.0  PYSEC-2026-4140 2.14.0
pyjwt   2.13.0  PYSEC-2026-4141 2.15.0
pyjwt   2.13.0  PYSEC-2026-4147 2.14.0
pyjwt   2.13.0  PYSEC-2026-4151 2.14.0
pyjwt   2.13.0  PYSEC-2026-4150 2.14.0
pyjwt   2.13.0  PYSEC-2026-4142 2.14.0
pyjwt   2.13.0  PYSEC-2026-4183 2.15.0
urllib3 2.7.0   PYSEC-2026-4177 2.8.0
urllib3 2.7.0   PYSEC-2026-4176 2.8.0
urllib3 2.7.0   PYSEC-2026-4175 2.8.0

Name     Skip Reason
-------- ---------------------------------------------------------------
pycflare URL requirements cannot be pinned to a specific package version
```

## Additional inventory and preservation checks

- Django registry inspection under `conf.settings.test`: PASS — 67 app registrations, 88 repository models, 174 non-admin URL leaves. Migration loader reads all 49 repository migration definitions. Model relationships, constraints, indexes, admin registrations and dependencies are recorded in the inventory.
- Celery autodiscovery: PASS — six repository tasks register without dispatch. Schedule consistency: FAIL — four beat entries target unregistered `django.core.management.call_command`; two command arguments also differ from tracked command names. SF-03/SF-19/SF-21 own later repairs.
- Master checksum comparison: FAIL — recorded hash `f17c7bb0bf30a0ffeb9db57ed30a2fcd9a96ada162e110bb82f80ed4f1f0d62c`; actual `e4cf7f962f62c9f9e97bf60440019b9cf3c0302e46e2c3c433541c561fd39eeb`. The file has LF line endings; changing normalization does not explain the discrepancy. Master bytes equal `git show HEAD:docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md`. Human provenance review required; do not regenerate the checksum merely to hide the failure.
- Initial git state: PASS — branch `work`, one worktree, empty status including untracked files. Final diff/preservation and documentation-link checks are recorded in the ledger.

## Checks not applicable or not established

No new unit/characterization tests were added because no behavior was replaced. Existing unit, API integration, authorization, idempotency and historical migration tests ran as part of the complete suite. No new database migration, index, backfill, caller cutover, observability hook or deletion is applicable to this documentation-only increment.

No PostgreSQL server, real Redis/Celery worker, live identity/storage/AI provider, frontend, deployment/IaC environment, restored backup or load fixture is supplied. PostgreSQL-specific queries/locks, asynchronous redelivery, provider integration, end-to-end clients, large-data migration/performance and restore/DR checks therefore remain unverified. No live infrastructure readiness or clean full security scan is claimed.

## Reviewer reproduction

The registry and scheduling evidence can be reproduced without sending jobs or querying a persistent database:

```bash
PYTHONPATH=app DJANGO_SETTINGS_MODULE=conf.settings.test uv run --locked python - <<'PY'
from pathlib import Path
import inspect
import django
django.setup()
from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.urls import URLResolver, get_resolver
from conf.celery import app

source_root = (Path.cwd() / "app").resolve()
local_models = [m for m in apps.get_models()
                if Path(inspect.getsourcefile(m)).is_relative_to(source_root)]
print("Apps:", len(list(apps.get_app_configs())))
print("Repository models:", len(local_models))
loader = MigrationLoader(None, ignore_no_migrations=True)
print("Repository migrations:", sum(
    Path(inspect.getsourcefile(type(m))).is_relative_to(source_root)
    for m in loader.disk_migrations.values()))

def leaves(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if route.startswith("admin/"):
            continue
        if isinstance(pattern, URLResolver):
            yield from leaves(pattern.url_patterns, route)
        else:
            yield route

print("Non-admin URL leaves:", len(list(leaves(get_resolver().url_patterns))))
app.autodiscover_tasks(force=True)
print("Management-command task registered:",
      "django.core.management.call_command" in app.tasks)
PY
```

Expected output: 67 apps, 88 repository models, 49 repository migrations, 174 non-admin leaves, and `False` for the management-command task registration.

1. Inspect the documentation-only diff and unchanged application/master/lockfile bytes. Compare board rows: only SF-00 may be READY_FOR_REVIEW; no concern is APPROVED by this work.
2. Read current architecture plus the generated registry inventory; follow source paths for canonical candidates, legacy callers and data projections.
3. Sync locked default/dev dependencies with Python 3.14. Run each recorded command (including the full workflow formatting/lint paths). For production startup, use only the workflow’s synthetic environment.
4. Confirm the three existing CI failures: one formatting file, one health assertion, and dependency-audit advisories (the advisory feed may evolve). Confirm warnings and the master-checksum discrepancy are visible.
5. Review all ledger risks and next actions. Decide the authority provenance question and whether the characterized baseline is acceptable. Only a human may approve SF-00; SF-01/SF-02 remain unstarted until that approval and subsequent selection.
