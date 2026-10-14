# Podcast content and sports metadata

`apps.posts.podcasts.Podcast`, `Season` and `Episode` remain the canonical content
owners, with their existing Django labels and tables. A Season belongs to a root
Podcast; an Episode belongs to that root and optionally one of its Seasons.
Football metadata continues to use the existing Region, Country, League, Team,
Player and Match relationships. No second football database is introduced.

## Content and compatibility contracts

Publication status, visibility, premium/public release dates and `required_plan`
are explicit Episode fields. The existing memberships access policy consumes
them. Categories describe content and no longer select a commercial plan.

The historical `Category.tier` reference remains in responses for compatibility,
but is optional and read-only in dashboard/admin writes. New categories require
no Plan. Deleting an old referenced Plan clears this reference without deleting
the category or its content associations. Existing category UUIDs and slugs are
unchanged; new slugs use the category name and UUID.

Canonical dashboard writes continue to project release data into the legacy
`public_release_date`/`exclusive` fields. Legacy public release writes remain
supported. Legacy exclusive writes require an existing explicit `required_plan`
or entitlement-only visibility. Otherwise the dashboard returns a field error:
use canonical visibility, required_plan and release fields. It never chooses a
plan from a category or silently assigns the cheapest paid plan. Editing taxonomy
alongside a legacy release cannot replace an existing explicit Episode plan.

Legacy child-Podcast URLs and UUIDs remain compatibility records pointing to the
canonical Season. The existing child write service updates ownership atomically.
Direct canonical Season edits cannot change its Podcast or issued slug; use the
explicit legacy bridge for existing child moves. Model validation covers admin
forms and inline edits; the dashboard rechecks a fresh locked Season on update.
Bulk SQL/ORM updates bypass these form/service checks and require the audit below.

## Migration and rollout

The content migration map is:

| Previous representation | Canonical owner / retained bridge |
|---|---|
| Podcast | Same Podcast table and identifiers |
| Child Podcast used as a season | Season, with `legacy_podcast` bridge |
| Episode attached to child | Episode attached to root Podcast and Season |
| Category tier used as access input | Explicit Episode.required_plan, historically backfilled |
| Sports metadata tags | Existing structured content M2M relationships |

1. Back up the target database and verify its migration history before rollout.
   Test on a restored copy; no production database has been migrated by this work.
2. Existing `podcasts.0002` backfills explicit access from historical categories.
   Existing `podcasts.0003` expands Seasons, reconciles duplicate slugs and remaps
   legacy children. Keep those historical files unchanged. Do not rerun their
   data functions against current editorial data: they intentionally describe
   the historical state, not a continual synchronization job.
3. Apply `category.0003_alter_category_slug_alter_category_tier`. It depends on
   `podcasts.0003`, makes the old tier nullable/SET_NULL and changes only future
   slug generation. It does not rewrite existing slugs or Episode access.
4. Deploy the complete SF-06 application and update staff clients to send explicit
   access fields. Avoid mixed old/new dashboard writers: old code still derives
   plans from categories and applies CASCADE deletion in the ORM.
5. Run the read-only JSON gate against the restored database and again at cutover:

   ```bash
   uv run --locked python app/manage.py audit_podcast_content --fail-on-drift --settings=conf.settings.production
   ```

   Inspect each nonzero count. Scheduled/hidden owning Podcasts may intentionally
   account for some publication findings; reconcile deliberately rather than
   automatically publishing content. Published PLAN episodes missing their plan
   require operator review; the audit does not grant access or change data.
6. Verify old Podcast/Episode URLs, Season filtering and representative sports
   relationships against saved pre-migration identifiers. Retain the child rows,
   legacy release projections and historical tier column until deployed data and
   client compatibility are confirmed. Runtime category access derivation is
   removed now; dropping compatibility data is a later reviewed contraction.

Rolling back the category schema is safe only when every category has an explicitly
reconciled tier: new tierless categories make the old NOT NULL column incompatible.
Do not invent plan associations or delete categories to reverse it. Prefer a
forward repair or a verified database restore coordinated with code rollback.
The existing Season migration can restore legacy Episode ownership on reversal;
duplicate-slug repair is not losslessly reversible. Preserve the backup and
identifier comparison results. No rollback has been applied to persistent data.

## Sports creation and operations

Missing Region/Country/League/Team display codes are assigned before the initial
insert; supplied codes (including zero) and slugs stay unchanged. Raw fixture
loads preserve supplied data. Candidate generation retries collisions at most
100 times and then fails visibly. Database uniqueness handles competing writers;
retry a failed write in a fresh transaction. This is not a new sports identifier.

Normal Match creation registers the existing Event/Possession initializer. It
creates only the empty structural rows expected by the existing serializer,
locks the Match and reuses any existing Event on a repeated call. Dashboard/admin
transactions include Match creation and these rows. A standalone ORM insert must
be wrapped in `transaction.atomic()` by its caller for the same all-or-nothing
guarantee. Raw imports and old Matches are not automatically backfilled with
invented score state; importers must supply their graph or deliberately initialize
it after verification. Live match behavior remains outside this concern.

No provider, media storage, worker queue, network service or new infrastructure
is introduced. Category access no longer adds category/plan selection queries.
Season editing and Match initialization use row locks; SQLite tests verify
transactions and replay behavior, not production PostgreSQL lock contention.
The content audit emits counts only and never includes subscriber or media data.

## Verification

Run the focused content, taxonomy, sports and migration tests, then the backend
workflow checks and full suite:

```bash
uv run --locked python app/manage.py test apps.posts.podcasts apps.category apps.region apps.match api.rest.dashboard.apps.podcasts api.rest.web.apps.podcasts --settings=conf.settings.test
uv run --locked python app/manage.py makemigrations --check --dry-run --settings=conf.settings.test
uv run --locked python app/manage.py test --settings=conf.settings.test
```

Tests cover legacy backfills/reversal, stable URLs/identifiers, access isolation,
Season ownership, taxonomy-only edits and plan deletion, audit failures, structured
sports relationships, collision retries and transaction rollback. The execution
ledger records actual commands/results and the human review boundary.
