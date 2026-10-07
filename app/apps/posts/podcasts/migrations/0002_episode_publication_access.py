import django.db.models.deletion
from django.db import migrations, models


def backfill_episode_publication_access(apps, schema_editor):
    """Deterministically preserve intentional legacy release/access semantics."""

    Episode = apps.get_model("podcasts", "Episode")
    Plan = apps.get_model("memberships", "Plan")
    database = schema_editor.connection.alias
    paid_fallback_id = (
        Plan.objects.using(database)
        .filter(tier__gt=0)
        .order_by("tier", "pk")
        .values_list("pk", flat=True)
        .first()
    )

    episodes = Episode.objects.using(database).select_related("podcast").all()
    for episode in episodes.iterator(chunk_size=500):
        plan_ids = set(episode.categories.using(database).values_list("tier_id", flat=True))
        plan_ids.update(
            episode.podcast.categories.using(database).values_list("tier_id", flat=True)
        )
        plan_candidates = Plan.objects.using(database).filter(pk__in=plan_ids)
        if episode.exclusive:
            plan_candidates = plan_candidates.filter(tier__gt=0)
        required_plan_id = (
            plan_candidates.order_by("-tier", "pk").values_list("pk", flat=True).first()
        )
        if episode.exclusive and required_plan_id is None:
            required_plan_id = paid_fallback_id

        release_at = episode.public_release_date
        Episode.objects.using(database).filter(pk=episode.pk).update(
            status="published" if release_at is not None else "draft",
            visibility="plan" if episode.exclusive else "public",
            premium_available_at=release_at,
            public_available_at=None if episode.exclusive else release_at,
            required_plan_id=required_plan_id,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("category", "0002_initial"),
        ("memberships", "0001_initial"),
        ("podcasts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="premium_available_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="episode",
            name="preview_duration_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="episode",
            name="public_available_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="episode",
            name="required_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="required_episodes",
                to="memberships.plan",
            ),
        ),
        migrations.AddField(
            model_name="episode",
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
            model_name="episode",
            name="visibility",
            field=models.CharField(
                choices=[
                    ("public", "Public"),
                    ("members", "Members"),
                    ("plan", "Plan"),
                    ("entitlement", "Entitlement"),
                ],
                db_index=True,
                default="public",
                max_length=16,
            ),
        ),
        migrations.RunPython(
            backfill_episode_publication_access,
            migrations.RunPython.noop,
        ),
        migrations.AddIndex(
            model_name="episode",
            index=models.Index(
                fields=["status", "public_available_at"],
                name="podcast_ep_public_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="episode",
            index=models.Index(
                fields=["status", "visibility", "premium_available_at"],
                name="podcast_ep_access_idx",
            ),
        ),
    ]
