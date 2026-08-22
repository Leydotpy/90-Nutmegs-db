from django.contrib import admin

from .models import Transcription, TranscriptionBillingRecord, UserTranscriptionQuota


class TranscriptionAdmin(admin.ModelAdmin):

    list_display = ('id', 'episode__title', 'language', 'provider', 'created_at')

    def get_readonly_fields(self, request, obj = ...):
        return obj._meta.get_fields()

    class Meta:
        model = Transcription


class TranscriptionBillingRecordAdmin(admin.ModelAdmin):

    class Meta:
        model = TranscriptionBillingRecord

    def get_readonly_fields(self, request, obj = ...):
        return obj._meta.get_fields()


class UserTranscriptionQuotaAdmin(admin.ModelAdmin):
    class Meta:
        model = UserTranscriptionQuota

    def get_readonly_fields(self, request, obj = ...):
        return obj._meta.get_fields()


admin.site.register(Transcription, TranscriptionAdmin)
admin.site.register(TranscriptionBillingRecord, TranscriptionBillingRecordAdmin)
admin.site.register(UserTranscriptionQuota, UserTranscriptionQuotaAdmin)