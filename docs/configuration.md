# Settings and secret handling

`conf.settings.base` owns shared configuration; `development`, `test` and
`production` own their environment overrides. `conf.settings.environment` wraps
python-decouple parsing with errors that name the setting without echoing supplied
values. OS environment variables override a local `.env`. No secret manager, second
settings registry or provider-domain implementation is introduced.

## Select the environment

Use an exported `DJANGO_SETTINGS_MODULE` or Django's `--settings` option:

```bash
uv run --locked python app/manage.py check --settings=conf.settings.development
uv run --locked python app/manage.py check --settings=conf.settings.test
```

`manage.py` defaults to development. WSGI, ASGI and Celery default to production.
The deprecated `conf.settings` and `conf.settings.local` development aliases remain
for compatibility. A `DJANGO_SETTINGS_MODULE` line inside `.env` cannot select the
module: Django selects it before python-decouple reads that file.

Copy `.env.example` only for local development and replace placeholders for services
you actually use. Development uses SQLite/locmem unless explicitly configured, and
supports local HTTP browser origins/cookies. Tests use in-memory SQLite, locmem,
eager Celery, synthetic identity/callback secrets and disabled external media
credentials. Unit tests do not prove real services are reachable.

## Production configuration boundary

Production always disables DEBUG and enables secure session/CSRF/history/queue
cookies. Missing required values and malformed security/service configuration stop
startup. Example/development secret prefixes (`replace-`, `change-me`, `unsafe-`)
are rejected for required secrets; this is not an entropy or credential-validity
test. Inject unique random credentials through deployment secrets, never source
control, command arguments, tickets or logs.

| Group | Required variables / policy |
|---|---|
| Django | `DJANGO_SECRET_KEY` (50+ characters), `DJANGO_ALLOWED_HOSTS` (hostnames/IPs; no global wildcard, scheme, path or port) |
| Database | `DATABASE_URL`, PostgreSQL URL with host and database; optional nonnegative `DATABASE_CONN_MAX_AGE` defaults to 60 seconds |
| Cache and broker | `REDIS_URL`, `CELERY_BROKER_URL`, each `redis://` or `rediss://` with host/valid port and nonnegative database number, including a query `db` override |
| Identity | `CLERK_SECRET_KEY`, nonempty `CLERK_AUTH_PARTIES` containing exact HTTPS origins |
| Giffy | `GIFFY_SHARED_SECRET` (32+ characters), `MAIN_PUBLIC_BASE_URL`, `GIFFY_API_BASE_URL` (exact HTTPS origins); positive finite `GIFFY_TIMEOUT_SECONDS` defaults to 30 |
| Media selection | `MEDIA_STORAGE_PROVIDER=cloudflare_r2`, `IMAGE_PLATFORM_PROVIDER=cloudflare_images`, `VIDEO_PLATFORM_PROVIDER=cloudflare_stream` |
| Cloudflare access | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` |
| R2 topology | Distinct `R2_PRIVATE_BUCKET_NAME` / `R2_PUBLIC_BUCKET_NAME`; `R2_PUBLIC_BASE_URL` must be a production HTTPS custom domain; `MEDIA_FILEFIELD_R2_CUTOVER_CONFIRMED=true` only after the existing object-copy/reconciliation gate is actually satisfied |
| Images/Stream | `CLOUDFLARE_IMAGES_ACCOUNT_HASH`, `CLOUDFLARE_IMAGES_SIGNING_KEY`, `CLOUDFLARE_STREAM_CUSTOMER_CODE`, `CLOUDFLARE_STREAM_SIGNING_KEY_ID`, `CLOUDFLARE_STREAM_SIGNING_PRIVATE_KEY_B64` (base64-encoded unencrypted RSA PEM, at least 2048 bits), `CLOUDFLARE_STREAM_WEBHOOK_SECRET` |
| Media browser policy | Nonempty `MEDIA_UPLOAD_ALLOWED_ORIGINS` (HTTPS origins) and `CLOUDFLARE_STREAM_ALLOWED_ORIGINS` (playback DNS hostnames, not URLs) |

The existing `CloudflareMediaConfig` remains the canonical provider validator.
Its upload URL lifetime is 120–21,600 seconds; private URL lifetime is 1–86,400
seconds; byte limit must be positive; duration limit is 1–36,000 seconds. No provider
request is made during configuration validation. Cache failures retain the existing
miss/fallback behavior and readiness signal; this work does not change access policy.

`CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` default to empty in production.
When needed, use comma-separated exact HTTPS origins, with optional valid ports;
wildcards, credentials, paths, queries and fragments are rejected. Development
honors explicit environment values and otherwise allows the existing localhost
CORS origins. Test settings reset both lists to empty.

Legacy CloudFront signing remains optional. Configure `CLOUDFRONT_DOMAIN`,
`CLOUDFRONT_COOKIE_DOMAIN`, `CLOUDFRONT_KEY_PAIR_ID` and `CLOUDFRONT_PRIVATE_KEY`
together, with a concrete API host sharing the narrow cookie domain. Existing
positive cookie lifetime/cache-margin validation remains. Active S3 presign and
preview lifetimes must be positive. Legacy AWS/AI credentials remain optional;
this concern does not enable offline DRM or migrate provider objects.

## HTTPS, proxy trust and rollout

**Existing TLS-terminating proxy deployments must explicitly configure
`TRUST_PROXY_SSL_HEADER=true` before rolling out this change.** Do so only when the
trusted proxy strips/replaces client-supplied `X-Forwarded-Proto`, writes `https`
for HTTPS traffic and prevents public access to the application port. With false
(the new default), Django ignores that header. An existing TLS proxy that relies on
it can otherwise cause an HTTPS redirect loop. Direct TLS deployments can leave it
false. `SECURE_SSL_REDIRECT` defaults true; exact `/health/live/` and `/health/ready/`
paths retain their existing private-HTTP probe exemptions.

HSTS now starts with `SECURE_HSTS_SECONDS=0`,
`SECURE_HSTS_INCLUDE_SUBDOMAINS=false`, `SECURE_HSTS_PRELOAD=false`. Verify HTTPS,
certificate renewal, redirects and affected domains before enabling a short HSTS
lifetime, then increase it as appropriate. Include subdomains only after verifying
every affected subdomain. Preload requires at least 31,536,000 seconds and
include-subdomains; setting the flag does not submit a domain to a preload list.
`check --deploy` warns while HSTS is disabled; do not suppress that warning without
an operational decision. CI uses an explicitly synthetic verified-TLS posture.

Before deployment:

1. Supply valid credentials, exact public/Giffy HTTPS endpoints, trusted hosts and
   browser origins; verify the existing R2 cutover evidence. Startup validation is
   not permission to assert an unperformed cutover.
2. Configure proxy trust and the chosen HSTS rollout policy. Restart web and worker
   processes with the same injected configuration, then run
   `uv run --locked python app/manage.py check --deploy --settings=conf.settings.production`
   inside that environment. Do not print the environment or `diffsettings` into logs.
3. Verify HTTPS redirects/cookies through the actual proxy and check health routes,
   database/cache readiness, workers and provider connectivity using authorized
   deployment procedures. Synthetic startup checks do not establish those facts.

There are no database migrations or backfills. Roll back code/configuration together;
keep newly provisioned secrets/endpoints valid across a rolling deployment. Restore
an explicit reviewed proxy/HSTS policy with any old version, whose defaults differ.
Browsers retain HSTS until expiry; reverting code does not immediately undo it.

## Rotation and logging

For Django signing-key rotation, inject a new `DJANGO_SECRET_KEY` and put the prior
key in comma-separated `DJANGO_SECRET_KEY_FALLBACKS` (each 50+ characters). Restart
all processes, verify old signatures remain readable, then remove old keys after
their maximum validity window. The tests exercise that verification. Do not log
fallback values. Provider/webhook secrets need their provider-specific overlap and
revocation procedure; this patch does not invent dual-secret verification where
the provider/client does not support it.

`conf.logging.RedactingFormatter` formats to stderr after replacing configured
secrets, credential URLs, authorization/cookie fields, signed/upload media URLs,
private-key blocks and labelled webhook payloads, including exceptions and stacks.
Django, application, Celery/task and multiprocessing handlers use it; Celery's
root-logger hijacking is disabled. It replaces Django's default email/error handlers
with the configured console handler. Existing external log collection must ingest
stderr; no new telemetry service or alert delivery is configured.

Log event names, internal IDs, outcomes and durations. Never log raw credentials,
request/response bodies, payment/webhook payloads, signed URLs or private keys.
Redaction is a fallback for accidental disclosure, not permission to log them.
It preserves shared LogRecords and reads current canonical settings per record
(processes still require restart after environment changes). It has no network/DB
access, but adds work proportional to message size and configured secrets; no
production throughput claim is made. Arbitrary unlabelled private data, opaque
custom capability paths, direct `print`/stderr and externally configured handlers
remain caller/operator responsibilities. Do not enable production SQL/HTTP wire
debug logging without separately reviewing the output.

`.gitignore` excludes `.env` and `.env.*` while retaining `.env.example`. Configured
production credentials, deployment topology, IAM grants, secret-manager audit trails
and credential rotation were not accessed or changed. No queue/storage/backup/cost
topology changes are part of this patch.

## Reviewer checks

```bash
uv run --locked python app/manage.py test conf.tests conf.test_configuration conf.test_logging --settings=conf.settings.test
uv run --locked python app/manage.py test --settings=conf.settings.test
uv run --locked python app/manage.py check --settings=conf.settings.development
uv run --locked python app/manage.py check --settings=conf.settings.test
uv run --locked python app/manage.py makemigrations --check --dry-run --settings=conf.settings.test
```

Use `.github/workflows/backend.yml` for exact formatting/lint/type/coverage and
synthetic production-startup commands. The configuration tests exercise malformed
values without disclosing them, local/production cookie posture, signing-key
rotation and actual Django/Celery logging setup without starting a worker. See the
single implementation ledger for results, remaining baseline failures and approval
state. Live PostgreSQL locking, provider integration, deployed proxy behavior and
throughput remain for their owning concerns.
