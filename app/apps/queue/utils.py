# apps/queue/utils.py
from .models import Queue

def get_or_create_queue_for_request(request) -> Queue:
    user = getattr(request, "user", None)
    # if user is logged in
    if user and user.is_authenticated:
        queue, _ = Queue.objects.get_or_create(owner=user)
        return queue
    # if user is anonymous
    # ensure a session key exists, if not, create one
    if not request.session.session_key:
        request.session.save()

    session_key = request.session.session_key

    # get queue by session key or create one
    queue, _ = Queue.objects.get_or_create(session_key=session_key)
    return queue