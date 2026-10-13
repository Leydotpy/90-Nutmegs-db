# apps/queue/signals.py
from django.contrib.auth.signals import user_logged_in
from django.core import signing
from django.db import transaction
from django.dispatch import receiver

from .models import Queue, QueueItem

ANON_COOKIE_NAME = "anon_qid"
signer = signing.Signer(salt="anon-queue-salt")


@receiver(user_logged_in)
def merge_anon_queue_to_user(sender, user, request, **kwargs):
    # Django rotates the session before emitting user_logged_in. Middleware keeps
    # the original server-owned identity for this request only.
    session_key = getattr(request, "_anonymous_session_key", request.session.session_key)
    request._anonymous_session_key = None
    if not session_key:
        return

    try:
        anon_q = Queue.objects.get(session_key=session_key, owner__isnull=True)
    except Queue.DoesNotExist:
        return

    with transaction.atomic():
        user_q, _ = Queue.objects.select_for_update().get_or_create(owner=user)
        # move items across, skipping duplicates
        existing_track_ids = set(user_q.items.values_list("track_id", flat=True))
        anon_items = list(anon_q.items.order_by("position", "added_at", "pk"))
        new_items = [item for item in anon_items if item.track_id not in existing_track_ids]
        positions = user_q._calculate_positions(len(new_items))
        to_move = []
        for item, position in zip(new_items, positions, strict=False):
            if item.track_id in existing_track_ids:
                continue
            to_move.append(
                QueueItem(
                    queue=user_q,
                    track_id=item.track_id,
                    position=position,
                    order=position,
                )
            )
            existing_track_ids.add(item.track_id)
        if to_move:
            QueueItem.objects.bulk_create(to_move)
            user_q.touch()
        # delete anon queue and items
        anon_q.delete()
