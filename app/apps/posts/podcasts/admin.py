from django.contrib import admin

from apps.media.audio.models import Audio
from apps.posts.podcasts.models import Episode, Podcast, Season
from apps.posts.podcasts.services import (
    resolve_canonical_episode_owner,
    synchronize_legacy_podcast_season,
)


class AudioInline(admin.StackedInline):
    model = Audio
    can_delete = True
    extra = 0
    readonly_fields = (
        "duration",
        "size_bytes",
        "sample_rate",
        "bitrate",
        "codec",
        "quality",
        "processed",
    )


class SeasonInline(admin.TabularInline):
    model = Season
    fk_name = "podcast"
    extra = 0
    fields = ("title", "slug", "number", "position", "published_at")


class PodcastAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "published_at",
        "structure",
        "slug",
        "timestamp",
    )
    list_display_links = ('id', 'title')
    list_filter = ("status", "language", "explicit_content", "structure")
    readonly_fields = ("id", "slug", "timestamp", "updated")
    inlines = [SeasonInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        synchronize_legacy_podcast_season(obj)

    class Meta:
        model = Podcast


class EpisodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "podcast__title",
        "season",
        "title",
        "status",
        "published_at",
        "timestamp",
    )
    list_display_links = ('id', 'title')
    list_filter = ("status", "visibility", "episode_type", "explicit_content")
    readonly_fields = ('id', 'slug', 'timestamp', 'updated', 'trend_score')
    inlines = [AudioInline]

    def save_model(self, request, obj, form, change):
        obj.podcast, obj.season = resolve_canonical_episode_owner(
            podcast=obj.podcast,
            season=obj.season,
        )
        super().save_model(request, obj, form, change)

    class Meta:
        model = Episode


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("id", "podcast", "title", "number", "position", "published_at")
    list_filter = ("podcast",)
    list_select_related = ("podcast", "legacy_podcast")
    readonly_fields = ("id", "legacy_podcast", "created_at", "updated_at")


admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Podcast, PodcastAdmin)
