import uuid

from django.db import models


class Chapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    episode = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    start_time = models.FloatField()  # seconds

    def __str__(self):
        return self.title