# Application and worker processes

SF-03 supplies separate process commands within the existing Django/Celery
application. `app/run_process.py` owns launch arguments;
`app/conf/task_queues.py` owns queue declarations, routing and the existing
scheduled entries. Domain task bodies and the canonical health handlers remain
their existing owners. No deployment or persistent database change has been
performed. The [implementation ledger](../SANFOOTBALL_IMPLEMENTATION_STATUS.md)
records validation and approval state.

## Installation and commands

Use CPython 3.14.8 on Linux x86_64, the exercised target, and the committed
`uv.lock`. Install each role into a separate environment or immutable image using
the profiles in [dependencies.md](dependencies.md). The repository root is the
working directory for these examples:

```sh
# Web, ordinary/bulk worker, scheduler, or ordinary administrative commands.
uv sync --locked --no-dev

# Instead, for the existing audio/offline processing worker:
uv sync --locked --no-dev --extra media-workers

# Instead, for an explicitly invoked recommendation training job:
uv sync --locked --no-dev --extra recommendation-workers
```

These are alternative installation profiles, not successive commands for a
running shared environment. `uv sync` removes packages outside the chosen
profile. The media compatibility extra includes managed transcription SDKs;
FFmpeg/ffprobe remain separate system dependencies. No transcription/model
training runs at web startup. The current audio pipeline includes transcription
within its media task, so there is no invented standalone transcription task or
queue. Later domain work can add separate routing when that boundary exists.

After installation, run exactly one role per deployment unit:

```sh
uv run --locked --no-sync python app/run_process.py web
uv run --locked --no-sync python app/run_process.py worker-default
uv run --locked --no-sync python app/run_process.py worker-media
uv run --locked --no-sync python app/run_process.py worker-bulk
uv run --locked --no-sync python app/run_process.py scheduler
uv run --locked --no-sync python app/run_process.py admin check --deploy
```

The launcher defaults to `conf.settings.production` and changes to the `app/`
directory before replacing itself with the selected process. Supply required
configuration through the environment as described in
[configuration.md](configuration.md); commands must not contain credentials.
An explicitly set `DJANGO_SETTINGS_MODULE` takes precedence. Development users
can select `conf.settings.development`; test settings are only for tests.
Administrative commands are explicit one-off jobs; application startup never
runs migrations, dataset generation or training automatically.

Inspect arguments without importing Django, requiring production credentials or
starting work:

```sh
uv run --locked --no-sync python app/run_process.py --dry-run web
uv run --locked --no-sync python app/run_process.py --dry-run worker-media
uv run --locked --no-sync python app/run_process.py --dry-run scheduler
```

`--dry-run` must precede the role. Web and worker roles accept `--concurrency`
from 1 to 32. Web also accepts `--bind` (default `0.0.0.0:8000`). The upper bound
is an input guard, not a recommendation to run 32 processes. Operators must size
concurrency against CPU, memory, temporary disk, database connections and provider
quotas before increasing it.

## Process and resource profiles

| Role | Default process profile | Work and resource behavior |
|---|---|---|
| Web | Gunicorn, 2 synchronous workers | 60-second worker timeout, 30-second graceful timeout; recycle after 1,000 requests plus up to 100 jitter. No embedded worker or scheduler. |
| Ordinary worker | Prefork, concurrency 2, queue `celery` | Ordinary tasks, CloudFront signing and fixed expiry/device maintenance wrappers; child recycling threshold 512 MiB. |
| Media worker | Prefork, concurrency 1, queue `media` | Audio pipeline and both existing offline package tasks; child recycling threshold 4 GiB. Install media extras and system tools. |
| Bulk worker | Prefork, concurrency 1, queue `bulk` | Trending/affinity recalculation and orphan package maintenance; child recycling threshold 2 GiB. Current SQL tasks do not require scientific extras. |
| Scheduler | One Celery beat process | Existing database-backed scheduler; no task execution and no local schedule file. Requires the normal Django database. |
| Administrative job | One explicit Django command | Run with the dependencies/resources needed by that command. Training and dataset commands load optional libraries only when invoked. |

All worker profiles use prefetch multiplier 1, a 1,740-second soft task limit,
1,800-second hard task limit and recycling after 100 tasks. These are bounds on
Celery prefork execution, not a new domain retry or idempotency policy. Existing
task acknowledgements, retries and failure behavior remain unchanged. Prefetch
limits reservation pressure but does not cap queue length or guarantee fairness.

Celery's `--max-memory-per-child` is measured in KiB and recycles a child after
its task completes. It **does not enforce a hard memory ceiling during a task**.
Set deployment CPU/memory reservations and hard limits separately, with headroom
for the parent, all children and their subprocesses. Also enforce temporary-disk
quotas and process/network permissions in the deployment platform. The launcher
does not create containers, cgroups, disk quotas or autoscaling policies.

Killing a Celery child does not by itself establish cleanup of all independently
spawned FFmpeg/provider work. Existing media subprocess timeout, scratch cleanup,
retry/idempotency and artifact lifecycle gaps remain with SF-13/SF-15/SF-19;
deployment capacity enforcement belongs to SF-21/SF-27. Do not infer measured
production capacity from these conservative starting profiles.

## Shutdown and health

The launcher uses `exec`, so supervisors signal the actual Gunicorn/Celery
process. Send `SIGTERM` for orderly shutdown. Gunicorn stops accepting new work
and allows its configured 30-second graceful period; give it at least 40 seconds
before a supervisor forces termination. Celery uses warm shutdown to stop
consuming and wait for active tasks. To accommodate the configured hard task
limit, provision at least 1,830 seconds of termination grace where supported.
Repeated signals or a shorter platform deadline can abort in-flight work.

Where the platform cannot supply that worker grace, drain the target worker's
consumer and confirm its active/reserved work is empty before replacing it.
An idle termination test does not prove safe interruption of billing, media,
provider or database work. Inspect task state and existing acknowledgement/retry
semantics before redelivery; do not blanket-retry jobs as a shutdown strategy.
One-off administrative jobs need their own supervisor deadline and operational
interruption plan because they are not Celery tasks.

Existing HTTP health contracts are unchanged:

- `GET /health/live/`: process-only liveness, with no database/cache/provider
  checks. Optional provider outages must not create liveness restart loops.
- `GET /health/ready/`: database `SELECT 1` and short-lived cache round trip;
  returns HTTP 503 with sanitized dependency status when unavailable.

These endpoints do not assert broker reachability, worker availability, provider
health or successful media processing. Use worker process state, broker consumer
and queue inspection, and deployment monitoring for those signals. Keep worker
and scheduler checks separate from public web readiness. Health routes alone do
not establish a production deployment or capacity acceptance gate.

Django, Celery and Gunicorn error handlers use the approved central redacting
formatter and emit to stderr. Gunicorn access logging is not enabled by the
launcher. External collectors/handlers and direct prints still need their own
privacy controls. No new log collector, metrics exporter or alert deployment is
included.

## Queue and scheduler rollout

The historical ordinary queue remains `celery`; heavy tasks now route to
`media` or `bulk`. Task identities are preserved. Producers and workers must use
the same routing map. Automatic creation of unknown queues is disabled so a
misspelled/undeclared destination fails visibly instead of accumulating work on
an unconsumed queue.

Use this deployment order after reviewing configuration and staging evidence:

1. Record broker queue depths, active/reserved work, deployed worker identities,
   current beat rows and database backup/restore readiness. Review custom
   `django-celery-beat` rows and explicit queue/exchange overrides; the static map
   cannot migrate an operator-created schedule or published message.
2. Deploy compatible ordinary, media and bulk workers before changing producers.
   Verify consumers are attached to all three queues and that media workers have
   their required SDKs/system tools. Keep a legacy `celery` consumer capable of
   running heavy tasks until messages published before the routing change drain.
3. Deploy web/API and other producers with the new routing map. Observe backlog,
   oldest message age and failures separately per queue. Heavy messages already
   on `celery` stay there; they are not automatically moved to `media` or `bulk`.
4. Drain old `celery` messages and active/reserved heavy jobs before replacing the
   legacy mixed worker with the lightweight ordinary profile. Do not purge queues
   to make a deployment appear complete.
5. Deploy the scheduler only after the maintenance review below. Maintain exactly
   one active beat instance, and stop the old beat before starting its replacement
   to avoid duplicate publication. The database owns its durable schedule; the
   launcher's empty pidfile argument is not a distributed singleton lock.

Existing beat entry keys and intervals are preserved, including the misleading
`recalc-user-category-affinity-every-10-min` key whose actual interval remains
daily. Django/Celery timezone alignment is not changed here. The database scheduler
updates settings-backed entries by their existing names. Inspect persisted enabled
state, timing and any manual overrides during rollout; historical/custom rows are
not deleted or backfilled by this concern.

The old unregistered generic management-command target and invalid command names
are repaired to explicit registered tasks:

| Existing beat key | Executed target | Cadence |
|---|---|---|
| `recalc-user-category-affinity-every-10-min` | Existing PostgreSQL affinity task | Daily |
| `expire-licenses-daily` | Fixed wrapper for `expire_licenses` | Daily |
| `rotate-cloud-front-cookies` | Existing `CloudFront Audio HLS Signing Task` | Daily |
| `revoke-inactive-devices-weekly` | Fixed wrapper for `revoke_inactive_licenses`, 90-day device inactivity threshold | Weekly |
| `gc-orphan-packages-daily` | Fixed wrapper for `gc_orphaned_packages`, 30-day package age threshold | Daily |

**Repairing scheduler targets activates maintenance that previously failed to
execute.** This can expire licenses, revoke inactive devices, delete old packages
and update signing state. Task/command business bodies are unchanged; registration
is not evidence that every legacy operation is safe on deployed data.

Before enabling the repaired schedule, perform a dry review of candidate records
and affected storage objects using read-only queries, then run the commands on an
isolated staging database/storage fixture. These legacy commands do not provide a
`--dry-run` option. Record candidate counts, IDs, expected changes and outcomes,
including retained active licenses/packages. Verify rollback/restore readiness
with the data owner. In particular, orphan-package cleanup currently suppresses
storage deletion exceptions before deleting the database row; SF-19 owns that
legacy consistency issue. Do not point staging verification at production storage.
No maintenance command or persistent scheduler mutation was run by SF-03 work.

For rollback, stop beat and new producers first, then drain all published queues
using compatible workers. Keep consumers on `media`/`bulk` until those queues and
their active/reserved jobs are empty; old routing does not relocate messages.
Restore matching code, lock and role configuration as one release. Restoring
broken old scheduler targets is not a valid maintenance recovery procedure; keep
the scheduler stopped while reviewing the failure. No schema rollback is needed,
but task effects may require domain-specific recovery or a tested data restore.

## Reviewer verification

In an isolated development/test environment with the development profile:

```sh
uv run --locked python app/manage.py test \
  conf.test_runtime_isolation conf.test_task_queues \
  --settings=conf.settings.test
```

The runtime isolation probe rejects heavy scientific/transcription imports and
external I/O/subprocess side effects during WSGI/ASGI startup and liveness in all
three settings environments. Queue tests publish through Celery's memory transport,
check scheduler registration/routing and exercise fixed wrapper selection without
running maintenance. Process tests start an idle prefork worker on a memory broker
and a real local Gunicorn server, then exercise liveness/readiness and `SIGTERM`.
The ledger records actual runs; do not treat this command listing as a passed run.

These checks do not validate a real Redis broker, PostgreSQL concurrency,
in-flight task interruption, provider calls or production autoscaling. Optional
dependency import/numerical smoke tests are documented in
[dependencies.md](dependencies.md). Giffy/OpenAI placeholder behavior and domain
retry/idempotency defects remain explicitly recorded for SF-15/SF-18/SF-19;
changing process placement does not resolve them.
