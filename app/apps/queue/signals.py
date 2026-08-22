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
    session_key = request.session.session_key
    if not session_key:
        return

    try:
        anon_q = Queue.objects.get(session_key=session_key)
    except Queue.DoesNotExist:
        return

    with transaction.atomic():
        user_q, _ = Queue.objects.select_for_update().get_or_create(owner=user)
        # move items across, skipping duplicates
        existing_episode_ids = set(user_q.items.values_list("episode_id", flat=True))
        to_move = []
        for item in anon_q.items.all().order_by("order", "added_at"):
            if item.episode_id in existing_episode_ids:
                continue
            to_move.append(
                QueueItem(queue=user_q, episode_id=item.episode_id, added_at=item.added_at, order=item.order))
        if to_move:
            QueueItem.objects.bulk_create(to_move)
            user_q.touch()
        # delete anon queue and items
        anon_q.delete()
