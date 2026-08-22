from django.contrib import admin
from .models import Queue, QueueItem


class QueueItemInline(admin.StackedInline):
    model = QueueItem
    extra = 1


class QueueAdmin(admin.ModelAdmin):
    inlines = [QueueItemInline]

    class Meta:
        model = Queue


admin.site.register(Queue, QueueAdmin)
admin.site.register(QueueItem)