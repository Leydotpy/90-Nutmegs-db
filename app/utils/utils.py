import random
import string

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet


def generate_code(_range=24, klass=None, *, using=None):
    """Choose an unused display code, with bounded retries on collisions.

    Database uniqueness remains authoritative if concurrent writers choose the
    same candidate; callers must retry the failed write rather than reuse it.
    """
    for _ in range(100):
        code = "".join(random.choice(string.digits) for _ in range(_range))
        if klass is None or not klass._default_manager.db_manager(using).filter(code=code).exists():
            return code
    raise ValidationError("Could not allocate an unused code; retry the operation.")


def regen_id(_range=40):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(_range))


def format_duration(duration: float) -> str:
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{int(hours)}h")

    if minutes:
        parts.append(f"{int(minutes)}m")

    if seconds or not parts:
        parts.append(f"{int(seconds)}s")

    return ":".join(parts)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")


def get_random[T: models.Model](qs: QuerySet[T]) -> T | None:
    count = qs.count()
    if count > 0:
        return qs.all()[random.randint(0, count - 1)]
    return None
