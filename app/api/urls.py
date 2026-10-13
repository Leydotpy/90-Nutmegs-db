"""Public API entry point; preserve the established REST prefix."""

from django.urls import path

# A Django URL tuple preserves the historical application name without adding
# an instance namespace to resolver matches. Existing reverse() callers use it.
urlpatterns = [path("rest/", ("api.rest.urls", "rest", None))]
