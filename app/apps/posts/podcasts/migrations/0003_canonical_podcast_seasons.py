"""Expand canonical Podcast/Season/Episode content ownership safely.

Legacy child Podcast rows are retained as compatibility records. Their episodes
move to the root Podcast and receive an explicit Season foreign key so there is
only one canonical content owner after this migration.
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models

SEASON_NAMESPACE = uuid.UUID("2d335b64-8b0a-4fb6-a412-36a6eec4ae7d")


def _podcast_slug(primary_key, used):
    """Return a deterministic valid slug that is unique within ``used``."""

    stem = f"podcast-{str(primary_key).replace('-', '').lower()}"
    candidate = stem[:50]
    attempt = 1
    while candidate in used:
        suffix = f"-{attempt}"
        candidate = f"{stem[: 50 - len(suffix)]}{suffix}"
        attempt += 1
    return candidate


def _episode_slug(primary_key, used):
    """Return a deterministic UUID for a duplicate legacy Episode slug."""

    attempt = 0
    while True:
        candidate = uuid.uuid5(
            SEASON_NAMESPACE,
            f"sanfootball:episode-slug:{primary_key}:{attempt}",
        )
        if str(candidate) not in used:
            return candidate
        attempt += 1


def _reconcile_slugs(Podcast, Episode, database):
    reserved_podcast_slugs = {
        str(slug).strip()
        for slug in Podcast.objects.using(database)
        .exclude(slug__isnull=True)
        .exclude(slug="")
        .values_list("slug", flat=True)
    }
    claimed_podcast_slugs = set()
    generated_podcast_slugs = set()
    podcasts = Podcast.objects.using(database).order_by("timestamp", "pk")
    for podcast in podcasts.iterator(chunk_size=500):
        original = str(podcast.slug or "").strip()
        slug = original
        if not slug or slug in claimed_podcast_slugs:
            slug = _podcast_slug(
                podcast.pk,
                reserved_podcast_slugs | generated_podcast_slugs,
            )
            generated_podcast_slugs.add(slug)
        if slug != original:
            Podcast.objects.using(database).filter(pk=podcast.pk).update(slug=slug)
        if original:
            claimed_podcast_slugs.add(original)

    reserved_episode_slugs = {
        str(slug)
        for slug in Episode.objects.using(database).values_list("slug", flat=True)
    }
    claimed_episode_slugs = set()
    generated_episode_slugs = set()
    episodes = Episode.objects.using(database).order_by("timestamp", "pk")
    for episode in episodes.iterator(chunk_size=500):
        original = str(episode.slug)
        slug = episode.slug
        if original in claimed_episode_slugs:
            slug = _episode_slug(
                episode.pk,
                reserved_episode_slugs | generated_episode_slugs,
            )
            generated_episode_slugs.add(str(slug))
            Episode.objects.using(database).filter(pk=episode.pk).update(slug=slug)
        claimed_episode_slugs.add(original)


def backfill_canonical_content(apps, schema_editor):
    """Publish legacy podcasts, create Seasons, and remap legacy episodes."""

    Podcast = apps.get_model("podcasts", "Podcast")
    Season = apps.get_model("podcasts", "Season")
    Episode = apps.get_model("podcasts", "Episode")
    database = schema_editor.connection.alias

    _reconcile_slugs(Podcast, Episode, database)

    # Every row predating this migration was publicly queryable. Preserve that
    # contract while making all new rows default to DRAFT after the migration.
    podcasts = Podcast.objects.using(database).all()
    for podcast in podcasts.iterator(chunk_size=500):
        Podcast.objects.using(database).filter(pk=podcast.pk).update(
            status="published",
            published_at=podcast.timestamp,
        )

    Episode.objects.using(database).filter(
        published_at__isnull=True,
        public_release_date__isnull=False,
    ).update(published_at=models.F("public_release_date"))

    parent_ids = (
        Podcast.objects.using(database)
        .filter(structure="CHILD", parent_id__isnull=False)
        .exclude(parent_id=models.F("pk"))
        .order_by("parent_id")
        .values_list("parent_id", flat=True)
        .distinct()
    )
    for parent_id in parent_ids.iterator(chunk_size=100):
        parent = Podcast.objects.using(database).filter(pk=parent_id).first()
        if parent is None or parent.structure != "PARENT" or parent.parent_id is not None:
            # Invalid legacy graphs stay untouched and visible for reconciliation
            # instead of being silently attached to another non-root season.
            continue

        children = (
            Podcast.objects.using(database)
            .filter(
                structure="CHILD",
                parent_id=parent_id,
            )
            .order_by("timestamp", "pk")
        )
        for position, child in enumerate(children.iterator(chunk_size=100), start=1):
            season_id = uuid.uuid5(
                SEASON_NAMESPACE,
                f"sanfootball:season:legacy-podcast:{child.pk}",
            )
            season, _ = Season.objects.using(database).update_or_create(
                legacy_podcast_id=child.pk,
                defaults={
                    "id": season_id,
                    "podcast_id": parent_id,
                    "number": position,
                    "title": child.title,
                    "slug": child.slug,
                    "description": child.description,
                    "position": position,
                    "published_at": child.timestamp,
                },
            )
            Episode.objects.using(database).filter(podcast_id=child.pk).update(
                podcast_id=parent_id,
                season_id=season.pk,
            )


def restore_legacy_episode_ownership(apps, schema_editor):
    """Restore child-Podcast episode ownership if the migration is reversed."""

    Season = apps.get_model("podcasts", "Season")
    Episode = apps.get_model("podcasts", "Episode")
    database = schema_editor.connection.alias
    seasons = Season.objects.using(database).exclude(legacy_podcast_id__isnull=True)
    for season in seasons.iterator(chunk_size=500):
        Episode.objects.using(database).filter(season_id=season.pk).update(
            podcast_id=season.legacy_podcast_id,
            season_id=None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("podcasts", "0002_episode_publication_access"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="duration_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="episode",
            name="episode_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="episode",
            name="episode_type",
            field=models.CharField(
                choices=[("full", "Full"), ("trailer", "Trailer"), ("bonus", "Bonus")],
                default="full",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="episode",
            name="explicit_content",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="episode",
            name="published_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="explicit_content",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="podcast",
            name="language",
            field=models.CharField(db_index=True, default="en", max_length=35),
        ),
        migrations.AddField(
            model_name="podcast",
            name="published_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("scheduled", "Scheduled"),
                    ("published", "Published"),
                    ("archived", "Archived"),
                ],
                db_index=True,
                default="draft",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="podcast",
            name="website_url",
            field=models.URLField(blank=True),
        ),
        migrations.CreateModel(
            name="Season",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("number", models.PositiveIntegerField(blank=True, null=True)),
                ("title", models.CharField(max_length=220)),
                ("slug", models.SlugField(default=uuid.uuid4)),
                ("description", models.TextField(blank=True, null=True)),
                ("position", models.PositiveIntegerField(default=1)),
                (
                    "published_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "legacy_podcast",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="canonical_season",
                        to="podcasts.podcast",
                    ),
                ),
                (
                    "podcast",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seasons",
                        to="podcasts.podcast",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "published_at", "pk"),
            },
        ),
        migrations.AddField(
            model_name="episode",
            name="season",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="episodes",
                to="podcasts.season",
            ),
        ),
        migrations.RunPython(
            backfill_canonical_content,
            restore_legacy_episode_ownership,
        ),
        migrations.AlterField(
            model_name="episode",
            name="slug",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="slug",
            field=models.SlugField(default=uuid.uuid4, unique=True),
        ),
        migrations.AlterModelOptions(
            name="episode",
            options={
                "ordering": ("-published_at", "-timestamp"),
                "verbose_name": "Episode",
                "verbose_name_plural": "Episodes",
            },
        ),
        migrations.AddIndex(
            model_name="podcast",
            index=models.Index(
                fields=["status", "published_at"],
                name="podcast_public_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="season",
            index=models.Index(
                fields=["podcast", "published_at"],
                name="podcast_season_public_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="episode",
            index=models.Index(
                fields=["podcast", "season", "published_at"],
                name="podcast_ep_timeline_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.UniqueConstraint(
                fields=("podcast", "slug"),
                name="podcast_season_slug_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.UniqueConstraint(
                fields=("podcast", "position"),
                name="podcast_season_position_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.UniqueConstraint(
                condition=models.Q(number__isnull=False),
                fields=("podcast", "number"),
                name="podcast_season_number_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.CheckConstraint(
                condition=models.Q(position__gte=1),
                name="podcast_season_position_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="season",
            constraint=models.CheckConstraint(
                condition=models.Q(number__isnull=True) | models.Q(number__gte=1),
                name="podcast_season_number_positive",
            ),
        ),
    ]
