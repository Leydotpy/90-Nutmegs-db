from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
# from apps.forum.managers import DiscussionManager, ReplyManager
from apps.forum import utils
from apps.fields.autoslugfield import AutoSlugField


# Create your models here.

def media_upload_to(instance: "Reply", filename: str):
    name, ext = filename.rsplit(".", 1)
    if ext in utils.VIDEO_EXT:
        return f"replies/{instance.thread.name}/audios/{name}.{ext}"
    if ext in utils.AUDIO_EXT:
        return f"replies/{instance.thread.name}/videos/{name}.{ext}"
    return f"replies/{instance.thread.name}/images/{name}.{ext}"


class Discussion(models.Model):
    """
    A DISCUSSION MODEL ---
    A DISCUSSION IS STARTED BY A SIGNED-UP USER AT THE SITE'S FORUM
    WHICH OTHER SIGNED-UP USERS OF THE SITE'S FORUM CAN PARTICIPATE IN
    A DISCUSSION SHALL HAVE LAID DOWN RULES AND REGULATION WHICH SHALL BE
    ENFORCED BY THE SITE'S ADMINISTRATORS. VIOLATION OF THESE RULES SHALL BE
    SANCTIONED ACCORDINGLY
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discussions")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="discussion_participation")
    name = models.CharField(max_length=250)
    slug = AutoSlugField(populate_from=("name", "pub_date"))
    views = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="discussion_views")
    pub_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return self.name

    @property
    def view_count(self):
        return self.views.all().count()

    @property
    def participant_count(self):
        return self.participants.all().count()


class Reply(models.Model):
    """
    A REPLY TO A ONGOING DISCUSSION WHICH IS OF THREE TYPES
        - A USER MIGHT SEND AN IMAGE IN REPLY TO A DISCUSSION
        - A USER MIGHT SEND A STICKER IN REPLY TO A DISCUSSION
        - A USER MIGHT SEND A MESSAGE IN REPLY
    A USER WHO IS NOT A PARTICIPANT OF A DISCUSSION WOULD NOT BE ABLE TO MAKE
    CONTRIBUTIONS IN AN ONGOING DISCUSSION
    """

    class Type(models.TextChoices):
        IMAGE = 'IMG', _("Image")
        VIDEO = 'VDO', _("Video")
        STICKER = 'STK', _("Sticker")
        TEXT = 'TXT', _("TEXT")
        AUDIO = "AUD", _("Audio")

    msg_type = models.CharField(max_length=100, choices=Type.choices, default=Type.TEXT)
    thread = models.ForeignKey(Discussion, null=True, blank=True, related_name="replies", on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    media = models.FileField(upload_to=media_upload_to, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "Reply"
        verbose_name_plural = "Replies"
        ordering = ["-timestamp"]

    def __str__(self):
        return self.thread
