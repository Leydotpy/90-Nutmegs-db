"""Transitional content-publication services for the expand/backfill/switch window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Q

if TYPE_CHECKING:
    from .models import Episode


CANONICAL_EPISODE_ACCESS_FIELDS = frozenset(
    {
        "status",
        "visibility",
        "premium_available_at",
        "public_available_at",
        "published_at",
        "required_plan",
        "preview_duration_seconds",
    }
)
LEGACY_EPISODE_ACCESS_FIELDS = frozenset(
    {
        "public_release_date",
        "exclusive",
    }
)


def synchronize_episode_access_from_legacy(episode: Episode) -> Episode:
    """Map legacy release inputs without inferring access from taxonomy.

    This exists only so older dashboard clients remain safe during the migration.
    New code must write the canonical fields directly. Undated legacy rows are kept
    as drafts instead of preserving the old accidental paid access to incomplete
    content.
    """

    from .models import Episode

    if (
        episode.exclusive
        and episode.required_plan_id is None
        and episode.visibility != Episode.Visibility.ENTITLEMENT
    ):
        raise ValidationError(
            {
                "required_plan": (
                    "Use canonical visibility, required_plan and release fields "
                    "for exclusive content."
                )
            }
        )

    release_at = episode.public_release_date
    values: dict[str, object] = {
        "required_plan": episode.required_plan,
        "status": (
            Episode.PublicationStatus.PUBLISHED
            if release_at is not None
            else Episode.PublicationStatus.DRAFT
        ),
        "visibility": (Episode.Visibility.PLAN if episode.exclusive else Episode.Visibility.PUBLIC),
        "premium_available_at": release_at,
        "public_available_at": None if episode.exclusive else release_at,
        "published_at": release_at,
    }
    if episode.visibility == Episode.Visibility.ENTITLEMENT:
        # Legacy fields cannot represent an entitlement-only resource. Never
        # widen it to plan/public access during a compatibility round-trip.
        values.update(
            required_plan=None,
            visibility=Episode.Visibility.ENTITLEMENT,
            public_available_at=episode.public_available_at,
        )
    for field, value in values.items():
        setattr(episode, field, value)
    episode.save(update_fields=(*values, "updated"))
    return episode


def synchronize_episode_legacy_projection(episode: Episode) -> Episode:
    """Maintain the read-only legacy projection for canonical dashboard writes."""

    from .models import Episode

    release_at = episode.public_available_at or episode.premium_available_at or episode.published_at
    exclusive = episode.public_available_at is None and (
        episode.visibility != Episode.Visibility.PUBLIC or episode.premium_available_at is not None
    )
    episode.public_release_date = release_at
    episode.exclusive = exclusive
    episode.save(update_fields=("public_release_date", "exclusive", "updated"))
    return episode


def synchronize_legacy_podcast_season(podcast):
    """Project one legacy child Podcast write into its canonical Season.

    This compatibility bridge is intentionally called from explicit dashboard
    and admin write paths; it is not a model signal or hidden ``save`` side
    effect. Canonical Season writes do not create new legacy child rows.
    """

    from .models import Episode, Podcast, Season

    if podcast.structure != Podcast.Structure.CHILD or podcast.parent_id is None:
        return None

    with transaction.atomic():
        parent = Podcast.objects.select_for_update().get(pk=podcast.parent_id)
        if parent.structure != Podcast.Structure.PARENT or parent.parent_id is not None:
            raise ValidationError(
                "A legacy child Podcast must belong directly to a root Podcast marked as a parent."
            )
        season = Season.objects.select_for_update().filter(legacy_podcast=podcast).first()
        if season is None or season.podcast_id != parent.pk:
            last_values = Season.objects.filter(podcast=parent).aggregate(
                position=Max("position"),
                number=Max("number"),
            )
            position = (last_values["position"] or 0) + 1
            number = (last_values["number"] or 0) + 1
            if season is None:
                season = Season(
                    podcast=parent,
                    legacy_podcast=podcast,
                )
            season.position = position
            season.number = number

        season.podcast = parent
        season.title = podcast.title
        season.slug = podcast.slug
        season.description = podcast.description
        season.published_at = (
            podcast.published_at if podcast.status == Podcast.PublicationStatus.PUBLISHED else None
        )
        season.save()
        Episode.objects.filter(Q(podcast=podcast) | Q(season=season)).update(
            podcast=parent,
            season=season,
        )
        return season


def resolve_canonical_episode_owner(*, podcast, season=None):
    """Resolve an explicit Episode owner across the legacy child compatibility API.

    Older dashboard and admin clients may still submit the child Podcast identifier
    that represented a Season. Those explicit write paths call this helper so the
    persisted Episode always points at the root Podcast and canonical Season.
    """

    from .models import Podcast

    if podcast.structure == Podcast.Structure.CHILD:
        canonical_season = synchronize_legacy_podcast_season(podcast)
        if canonical_season is None:
            raise ValidationError("The legacy child Podcast has no canonical Season.")
        if season is not None and season.pk != canonical_season.pk:
            raise ValidationError(
                "The selected Season does not represent the legacy child Podcast."
            )
        return canonical_season.podcast, canonical_season

    if podcast.parent_id is not None:
        raise ValidationError("An Episode must belong to a root Podcast.")
    if season is not None and season.podcast_id != podcast.pk:
        raise ValidationError("The Season must belong to the selected Podcast.")
    return podcast, season
