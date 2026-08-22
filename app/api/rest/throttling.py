from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    rate = "60/min"


class SustainedRateThrottle(UserRateThrottle):
    rate = "1000/day"


class LiveMatchThrottle(UserRateThrottle):
    rate = "120/min"


class BurstUserThrottle(UserRateThrottle):
    scope = "burst_user"  # configure in settings


class SustainedUserThrottle(UserRateThrottle):
    scope = "sustained_user"


class AnonymousBurstThrottle(AnonRateThrottle):
    scope = "anon_burst"
