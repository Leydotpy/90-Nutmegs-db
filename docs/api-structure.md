# API structure and compatibility

The Django domain apps own models, migrations, signals and business behavior.
API packages own serializers, permissions, views and ordinary `urls.py` modules;
they are not registered Django apps. The existing feature folders beneath
`api/rest/web/apps` and `api/rest/dashboard/apps` remain the presentation boundary.
Use direct Python imports for known classes and Django's `apps.get_model()` only
when a model label is genuinely selected at runtime. There is no override loader.

Project URLs include `api.urls`, which includes the REST web and dashboard trees.
Keep URL names, application names, namespaces, router basenames and ordering
explicit. DRF router registrations stay beside the feature's URL patterns.
Domain `AppConfig.ready()` imports domain receivers only; entitlement response
serializer selection belongs to the memberships API module.

## Supported client contract

SF-04 retains the current `/api/rest/` versioning strategy. Its 174 non-admin
routes, callback classes, HTTP action mappings and permissions are characterized
in `app/conf/fixtures/api_structure_sf04.json`, captured before migration.
The corresponding tests also preserve 107 model/table identities and 84 admin
registrations. Removing 20 presentation-only AppConfigs leaves 47 registrations.
Internal Python imports of the deleted loader/configuration classes are retired;
all repository callers have migrated. Model labels and tables are unchanged.

SF-05 subsequently restricts dashboard permissions and replaces router-root view
classes with staff-protected equivalents. The historical fixture remains intact;
its test explicitly enumerates that security delta. See
[identity and authorization](identity-and-authorization.md) for the current rules.

No public route is deprecated or replaced, so no client migration or removal
date applies. A future version must record old/replacement routes, announced
deprecation and removal dates, and measured usage before retiring this tree.
This refactor does not imply all inherited endpoints satisfy their eventual
domain acceptance gates. In particular, the duplicate dashboard audio DELETE
and PATCH path, existing schema warnings and domain defects remain recorded in
the implementation ledger for their owners.

## Validation and rollback

Run `uv run --locked python app/manage.py test conf.test_api_structure
conf.test_model_loading conf.test_api_contracts conf.test_listener_journeys
--settings=conf.settings.test` (as one command), then the full backend workflow.
The startup probe rejects imports of the removed framework and verifies domain
startup no longer imports the API layer. The contract tests additionally exercise
HTTP requests and established reverse lookup aliases.

No database migration, backfill, provider call or persistent storage change is
required. Deploy the settings, URL modules and migrated callers together. Rollback
requires the complete previous application artifact; do not mix old settings
with deleted AppConfigs. Domain data, workers, task names, queues and operational
health endpoints are unaffected. Normal startup performs fewer imports; no new
query, cache, concurrency or infrastructure dependency is introduced.
