"""Admin registrations for promotion models."""

from __future__ import annotations

from django.contrib import admin

from .models import AutomaticPostList, HandPickedPostList, Image, MultiImage, OrderedPodcast, OrderedPostList


@admin.register(Image)
class ImagePromotionAdmin(admin.ModelAdmin):
    """Operational admin for remote image promotions."""

    list_display = (
        "id",
        "name",
        "title",
        "podcast",
        "banner_status",
        "banner_provider",
        "banner_output_format",
        "date_created",
    )
    list_filter = ("banner_status", "banner_provider", "banner_output_format", "banner_preset")
    search_fields = ("name", "title", "banner_job_id", "banner_url")
    readonly_fields = ("id", "banner_job_id", "banner_url", "banner_error", "rendered_at", "synced_at")


admin.site.register(HandPickedPostList)
admin.site.register(OrderedPostList)
admin.site.register(OrderedPodcast)
admin.site.register(AutomaticPostList)
admin.site.register(MultiImage)
