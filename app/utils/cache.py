from django.conf import settings
from django.core.cache import cache


REDIS_CACHE_TIMEOUT = getattr(settings, 'REDIS_CACHE_TIMEOUT', 3600)

def store(key, value):
    cache.set(key, value, REDIS_CACHE_TIMEOUT)

def retrieve(key):
    return cache.get(key)