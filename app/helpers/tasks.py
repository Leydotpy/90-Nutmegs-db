from functools import partial

from celery import Task
from django.db import transaction


def delay_on_commit(fn: Task, *args, **kwargs):
    delayed_fn = partial(fn.delay, *args, **kwargs)
    transaction.on_commit(delayed_fn)
