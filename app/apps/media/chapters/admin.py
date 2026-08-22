from django.contrib import admin

from .models import Chapter


class ChapterAdmin(admin.ModelAdmin):

    list_display = ('id', 'episode__title', 'title', "start_time")

    class Meta:
        model = Chapter


admin.site.register(Chapter, ChapterAdmin)