import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.memberships.access import get_user_highest_active_subscription
from core.compat import get_user_model

User = get_user_model()


class Language(models.TextChoices):
    ENGLISH = "en", _("English")
    FRENCH = "fr", _("French")
    SPANISH = "sp", _("Spanish")
    ARABIC = "ar", _("Arabic")
    GERMAN = "de", _("German")
    ITALIAN = "it", _("Italian")


class Transcription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    episode = models.OneToOneField("podcasts.Episode", on_delete=models.CASCADE, related_name="transcription")
    language = models.CharField(max_length=16, default=Language.ENGLISH)
    text = models.TextField()
    segments = models.JSONField(default=list, blank=True)
    provider = models.CharField(max_length=32, choices=(("openai", "OpenAI"), ("google", "Google")))
    audio_duration_seconds = models.PositiveIntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    # New file fields - optional (blank=True, null=True)
    srt_file = models.FileField(upload_to="transcripts/srt/", null=True, blank=True)
    vtt_file = models.FileField(upload_to="transcripts/vtt/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.episode)



class TranscriptionBillingRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    episode = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE)
    provider = models.CharField(max_length=32)
    audio_seconds = models.PositiveIntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.episode)


class UserTranscriptionQuota(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    used_seconds = models.PositiveIntegerField(default=0)
    period_start = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.user)

    @property
    def plan(self):
        return get_user_highest_active_subscription(self.user).membership.plan