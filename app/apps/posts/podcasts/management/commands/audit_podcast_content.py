import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q
from django.utils import timezone

from apps.posts.podcasts.models import Episode, Podcast


class Command(BaseCommand):
    help = (
        "Audit the canonical podcast, season, and episode relationships without "
        "changing data. Output is one JSON object suitable for deployment gates."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-on-drift",
            action="store_true",
            help="Exit with a CommandError when any canonical-content drift is found.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        legacy_children = Podcast.objects.filter(structure=Podcast.Structure.CHILD)
        discoverable_podcast_ids = Podcast.objects.discoverable(now=now).values("pk")

        counts = {
            "legacy_children_missing_explicit_season": legacy_children.filter(
                canonical_season__isnull=True
            ).count(),
            "legacy_children_with_mismatched_explicit_season": legacy_children.filter(
                canonical_season__isnull=False
            )
            .filter(Q(parent__isnull=True) | ~Q(canonical_season__podcast_id=F("parent_id")))
            .count(),
            "legacy_children_missing_parent": legacy_children.filter(parent__isnull=True).count(),
            "legacy_children_with_invalid_parent": legacy_children.filter(parent__isnull=False)
            .exclude(
                parent__structure=Podcast.Structure.PARENT,
                parent__parent__isnull=True,
            )
            .count(),
            "nonchild_podcasts_with_parent": Podcast.objects.exclude(
                structure=Podcast.Structure.CHILD
            )
            .filter(parent__isnull=False)
            .count(),
            "episodes_owned_by_legacy_child": Episode.objects.filter(
                podcast__parent__isnull=False
            ).count(),
            "episode_season_podcast_mismatches": Episode.objects.filter(season__isnull=False)
            .exclude(season__podcast_id=F("podcast_id"))
            .count(),
            "published_podcasts_missing_published_at": Podcast.objects.filter(
                status=Podcast.PublicationStatus.PUBLISHED,
                published_at__isnull=True,
            ).count(),
            "published_episodes_with_undiscoverable_podcast": Episode.objects.filter(
                status=Episode.PublicationStatus.PUBLISHED
            )
            .exclude(podcast_id__in=discoverable_podcast_ids)
            .count(),
        }
        drift_count = sum(counts.values())
        payload = {
            "checked_at": now.isoformat(),
            "counts": counts,
            "drift_count": drift_count,
            "drift_detected": drift_count > 0,
        }
        self.stdout.write(json.dumps(payload, sort_keys=True))

        if options["fail_on_drift"] and drift_count:
            finding_label = "finding" if drift_count == 1 else "findings"
            raise CommandError(
                f"Podcast canonical-content drift detected ({drift_count} {finding_label})."
            )
