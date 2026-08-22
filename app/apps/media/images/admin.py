from django.contrib import admin

from apps.media.images.models import Image


class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "filename", "size", "width", "height")
    list_filter = ("title", "timestamp", "size", "width", "height")
    search_fields = ("title", "filename", "size", "width", "height")
    list_display_links = ("id", "title")

    class Meta:
        model = Image
        fields = ("title", "id", "timestamp")



admin.site.register(Image, ImageAdmin)
