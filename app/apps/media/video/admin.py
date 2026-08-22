from django.contrib import admin

from .models import Video


class VideoAdmin(admin.ModelAdmin):
    class Meta:
        model = Video


admin.site.register(Video, VideoAdmin)