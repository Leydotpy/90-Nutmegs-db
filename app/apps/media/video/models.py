import uuid

from django.db import models


class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=200)
    duration = models.PositiveIntegerField(null=True, blank=True)
    codec = models.CharField(max_length=200, null=True, blank=True, default="mp4")
    file = models.FileField(upload_to="media/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
