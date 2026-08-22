from django.contrib import admin

from apps.media.models import PlayList, MediaSettings


class MediaSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user__username', )
    search_fields = ('user__username', )
    list_filter = ('user__username',)


    class Meta:
        model = MediaSettings


class PlayListAdmin(admin.ModelAdmin):
    class Meta:
        model = PlayList

admin.site.register(PlayList, PlayListAdmin)
admin.site.register(MediaSettings, MediaSettingsAdmin)
