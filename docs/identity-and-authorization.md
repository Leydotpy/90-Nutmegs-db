# Identity and authorization

`users.ClerkUser` remains the sole local user model. Its existing unique nullable
`clerk_user_id` is the external mapping; local operator accounts can remain
unmapped. There is no second identity table, migration or backfill.

`apps.accounts.identity` verifies each Clerk credential through the pinned SDK,
then resolves the verified subject by Clerk ID only. It does not use the SDK's
email-based account synchronization or token-to-user cache. JWT signature,
expiration, not-before, configured audience and authorized party checks remain
the SDK's responsibility; the local boundary additionally requires a subject
and unexpired token. Request-local reuse avoids duplicate verification within a
request. A fresh request rechecks verification and the local active flag.

On first sign-in, the provider profile must match the verified subject. A new
local user receives an unusable password, a deterministic unique username, names
and a verified primary email if present. Staff and superuser flags default false.
Repeated or competing first requests converge through the unique database key.
An email collision requires operator reconciliation; it never links or overwrites
another account. Existing usernames, local suspension, passwords, groups and
privileges remain unchanged. Profile updates are not silently synchronized on
every request. Provider metadata, roles and commercial claims do not grant local
permissions or bypass AccessPolicy.

## Credential and endpoint contract

All 172 DRF routes are covered by `conf.test_endpoint_authentication`:

| Endpoint family | Authentication and authorization |
| --- | --- |
| REST web discovery and published content | Explicit bearer first, otherwise browser session compatibility; anonymous reads where the view permits them; publication and access policies remain authoritative |
| Web playback, queue and profile | Same credential order; existing per-view authenticated/anonymous and ownership policies remain in force |
| Protected streaming and offline APIs | Same credential order; existing server AccessPolicy, device, owner and license checks remain in force |
| Interactive dashboard, including schema and router roots | Active local staff required; existing object/model permission checks remain additional requirements |
| Dashboard commercial resources and nested actions | Active staff reads; active staff superusers alone mutate plans, features, entitlements, memberships and subscriptions |
| Giffy provider callback | No end-user authentication; existing timestamp/body-checksum/HMAC verification remains mandatory |
| Django admin | Existing local Django authentication, staff flag and model permissions |
| Liveness/readiness | Public operational probes with their existing sanitized responses |

The common DRF settings deliberately specify `ClerkBearerAuthentication`, then
`SessionAuthentication`. A malformed or rejected explicit bearer is a 401 and
cannot downgrade to a session. Verification outages return a sanitized 503.
Clerk browser cookies use the same local identity boundary through middleware;
unsafe cookie/session requests still require CSRF. No new authentication route,
password/reset flow, role-management API or commercial-claim trust is introduced.
Existing API throttles remain; per-edge authentication abuse controls and provider
capacity measurements belong to the deployment/hardening concerns.

The local `is_staff` flag is the existing content-operator role. `is_superuser`
adds commercial administration. Operators assign these using Django admin, where
changes have Django's existing audit trail. No job-title permission scheme or new
role model is introduced. Do not grant flags from identity-provider claims.

## Audit and privacy

Interactive dashboard mutations write minimal actor, model, object ID, method,
action and route identifiers to Django's existing `admin.LogEntry`. The audit row
and database mutation share a transaction. Failed responses roll back database
writes; an audit storage failure also rolls them back. This does not roll back an
external provider action that already completed; provider retry/reconciliation
belongs to the media and promotions concerns. Logs contain no request bodies,
tokens, commercial notes or object display strings. Audit writes add one row per
successful mutation and a cached content-type lookup. Dynamic-queryset views
record their view class and route/target identifiers without an admin object
link. Existing provider-backed dashboard handlers hold this transaction while
they run; direct-upload and asynchronous provider lifecycle work remains SF-14
and SF-18.

Public user representations retain their small existing allowlist. Podcast
representations expose follower counts rather than full follower lists, including
dashboard and nested entitlement responses. Unsupported generic entitlement
targets return an opaque object ID without fetching or serializing the target;
passwords, license keys and arbitrary internal fields cannot leak through a
generic `__all__` fallback. Public membership/subscription representations use
explicit fields and exclude customer/provider references.

The identity mapping and first-sign-in profile fields support authentication and
display, not listener analytics. They follow the existing user record lifetime;
no separate behavioral, location or device data is collected. Audit access stays
within Django admin's existing model permissions. There is no newly invented
retention schedule: existing records remain until the repository's deletion and
retention processes act. User deletion cascades existing admin log references;
legal retention, anonymization and full domain deletion workflows require their
own reviewed policy before production rollout. No listener-level analytics are
made available to creators by this change.

## Login handoff and compatibility

Django rotates its session key before `user_logged_in`. The accounts session
middleware captures the original server-known anonymous key for login POSTs so
the existing queue merge can find it. Client-submitted queue/session IDs are
ignored. Read-only requests keep lazy session access, including zero-query liveness
with an existing session cookie when automatic session resaving is disabled.
The pre-existing global SESSION_SAVE_EVERY_REQUEST setting still writes sessions
for browser-cookie requests; operational health probes should omit cookies.
The receiver consumes the captured key once and only considers an
unowned queue. Failed login and switching already-authenticated users do not
claim another queue. Queue concurrency, anonymous API mutation policy and bearer
login merge remain with SF-11; no queue model or ordering redesign is included.

URLs and route names remain stable. Intentional access changes require clients
to use authorized staff for formerly open dashboard sports endpoints; commercial
`add_feature` now has the same superuser rule as other commercial mutations.
Follower-list fields and unsafe generic target representations are removed for
privacy. These are security restrictions, with no insecure compatibility alias.

Before deployment, review current local staff/superuser assignments and ambiguous
email-only accounts. Resolve identity conflicts through a reviewed operator
process using verified provider identity; do not bulk-link by email. Deploy the
middleware, adapter and local service together. No schema migration is needed.
Rolling back the whole artifact restores prior security weaknesses and is not a
recommended incident response; use a forward correction or temporarily disable
the affected route instead. Actual Clerk tenant configuration, token revocation
latency, provider network failure and PostgreSQL concurrent first sign-in still
require staging evidence. Local tests verify signatures and policy without live
provider credentials.

## Reviewer checks

Run the focused command as one line:

```sh
uv run --locked python app/manage.py test apps.accounts.test_identity conf.test_endpoint_authentication conf.test_staff_authorization conf.test_identity_privacy conf.test_login_identity api.rest.web.serializers.test_authentication --settings=conf.settings.test
```

Then run the full backend workflow. Review the historical SF-04 route fixture and
its explicit SF-05 permission delta; no path/action/migration changes are hidden
by regenerating the fixture. Inspect audit records for successful mutations and
confirm denied requests, invalid JWTs, suspension and CSRF checks fail closed.
