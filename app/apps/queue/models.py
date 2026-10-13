import typing

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.media.models import PlayList
from apps.posts.podcasts.models import Episode, Podcast

User = settings.AUTH_USER_MODEL


class AppLabel(models.TextChoices):
    PODCAST = "podcasts.Podcast", _("Podcast")
    EPISODE = "podcasts.Episode", _("Episode")
    PLAYLIST = "media.Playlist", _("Playlist")


class QueueQueryset(models.QuerySet):

    def open(self):
        return self.filter(date_merged__isnull=True)

    def merged(self):
        return self.filter(date_merged__isnull=False)


class OpenQueueManager(models.Manager):

    def get_queryset(self):
        return QueueQueryset(self.model, using=self._db).open()

    def get_or_create(self, **kwargs):
        return self.get_queryset().get_or_create(**kwargs)


class QueueManager(models.Manager):

    def get_queryset(self):
        return QueueQueryset(self.model, using=self._db)

    def open(self):
        return self.get_queryset().open()

    def merged(self):
        return self.get_queryset().merged()

    def ger(self):
        self.get_or_create()


class Queue(models.Model):
    date_merged = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="queues",
    )
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    frozen = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return str(self.pk)

    objects = QueueManager()
    open = OpenQueueManager()

    class Meta:
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["last_activity"]),
            models.Index(fields=["session_key"]),
        ]

        constraints = [
            models.CheckConstraint(
                check=(models.Q(owner__isnull=False) |
                       models.Q(session_key__isnull=False)
                       ),
                name="queue_must_have_owner"
            )
        ]

    def touch(self):
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    def is_anonymous(self):
        return self.session_key is not None and self.owner is None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._items = None

    def flush(self):
        self.items.all().delete()
        self._items = None

    @property
    def tracks(self):
        if self.id is None:
            return self.items.model.objects.none()
        if self._items is None:
            self._items = (
                self.items.select_related("track")
                .filter(track_id__in=Episode.objects.discoverable().values("pk"))
                .order_by(
                    "position",
                    "added_at",
                    "pk",
                )
            )
        return self._items

    def count(self):
        return self.tracks.count()

    @classmethod
    def _get_item(cls, item_id: str, app_label: str) -> Episode | PlayList | Podcast:
        label, model_name = app_label.split(".", maxsplit=1)
        model = apps.get_model(label, model_name)
        return get_object_or_404(model, pk=item_id)

    def _calculate_positions(self, count: int, override: bool = False) -> list[int]:
        """
        Calculates a list of integer positions for new items.
        """
        if count == 0:
            return []

        if override:
            # Prepend: Find current minimum and subtract
            current_min = self.items.aggregate(m=Min('position'))['m'] or 0
            # Keep the input order stable while placing the whole group before
            # the current first item.
            return list(range(current_min - count, current_min))

        # Append: Find current maximum and add
        current_max = self.items.aggregate(m=Max('position'))['m'] or 0
        # Result: [max+1, max+2, max+3...]
        return [current_max + (i + 1) for i in range(count)]

    def add_item(self, item_id: str, app_label: str, override: bool = False):
        """
        Handles logic for adding specific episodes or expanding podcasts into episodes.
        """
        obj = self._get_item(item_id, app_label)  # Assuming you have this helper method defined

        if isinstance(obj, PlayList) and obj.user_id is not None and obj.user_id != self.owner_id:
            raise ValueError("Playlist is not available for queueing")

        # 1. Prepare list of episodes to add
        episodes_to_add = []

        if isinstance(obj, Episode):
            if not Episode.objects.discoverable().filter(pk=obj.pk).exists():
                raise ValueError("Episode is not available for queueing")
            # Check if exists to prevent duplicates (optional logic based on your needs)
            if not self.items.filter(track_id=obj.id).exists():
                episodes_to_add = [obj]
        elif hasattr(obj, "get_discoverable_episodes"):
            # It is a Podcast/Collection
            # Filter out episodes that are ALREADY in the queue to avoid unique constraint errors
            existing_ids = set(self.items.values_list("track_id", flat=True))
            episodes_to_add = list(
                obj.get_discoverable_episodes().exclude(id__in=existing_ids)
            )
        else:
            raise ValueError(f"Object {obj} cannot be added to queue")

        if not episodes_to_add:
            return self

        # 2. Calculate Positions efficiently
        positions = self._calculate_positions(len(episodes_to_add), override=override)

        # 3. Prepare QueueItem objects
        queue_items = [
            self.items.model(
                queue=self,
                track_id=episode.id,
                position=position
            )
            for episode, position in zip(episodes_to_add, positions, strict=True)
        ]

        # 4. Bulk Create
        self.items.bulk_create(queue_items, batch_size=50)
        self._items = None

        return self

    def merge_item(self, item):
        if self.items.filter(track_id=item.track_id).exists():
            item.delete()
        else:
            item.queue = self
            item.position = self._calculate_positions(1)[0]
            item.order = item.position
            item.save(update_fields=["queue", "position", "order"])
        self._items = None

    merge_item.alters_data = True

    def merge(self, queue: typing.Self):
        for item_to_merge in queue.items.order_by("position", "added_at", "pk"):
            self.merge_item(item_to_merge)
        queue.date_merged = timezone.now()
        queue._items = None
        queue.save(update_fields=["date_merged"])

    merge.alters_data = True


class QueueItemQueryset(models.QuerySet):
    ...


class QueueItemManager(models.Manager):
    def get_queryset(self):
        return QueueItemQueryset(self.model, using=self._db)


class QueueItem(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name="items")
    track = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)  # use to keep queue order

    objects = QueueItemManager()

    def __str__(self):
        return str(self.track)

    class Meta:
        unique_together = ("queue", "track")
        ordering = ["order", "added_at"]
