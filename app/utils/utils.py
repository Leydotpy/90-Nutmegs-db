import random
import string
from typing import TypeVar

from django.db import models
from django.db.models import QuerySet


T = TypeVar('T', bound=models.Model)


def generate_code(_range=24, klass=None):
    code = "".join(random.choice(string.digits) for x in range(_range))
    if klass is not None:
        if klass.objects.filter(code=code).exists():
            generate_code(_range, klass)
    return code


def regen_id(_range=40):
    chars = string.ascii_uppercase+string.ascii_lowercase+string.digits
    return str().join(random.choice(chars) for _ in range(_range))

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
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_random(qs: QuerySet[T]) -> T | None:
    count = qs.count()
    if count > 0:
        return qs.all()[random.randint(0, count - 1)]
    return None