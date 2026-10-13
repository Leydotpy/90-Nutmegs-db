"""Atomic, minimal staff mutation records in Django's existing admin audit log."""

import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework.permissions import SAFE_METHODS


class StaffAuditMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.method in SAFE_METHODS:
            return super().dispatch(request, *args, **kwargs)
        with transaction.atomic():
            response = super().dispatch(request, *args, **kwargs)
            if 200 <= response.status_code < 300:
                queryset = getattr(self, "queryset", None)
                model = getattr(queryset, "model", None)
                data = getattr(response, "data", None)
                object_id = kwargs.get("pk")
                if object_id is None and isinstance(data, dict):
                    object_id = data.get("id")
                object_id = str(object_id) if object_id is not None else None
                label = model._meta.label if model else type(self).__name__
                LogEntry.objects.create(
                    user_id=self.request.user.pk,
                    content_type=ContentType.objects.get_for_model(model) if model else None,
                    object_id=object_id,
                    object_repr=f"{label}:{object_id or 'collection'}"[:200],
                    action_flag={"POST": ADDITION, "DELETE": DELETION}.get(request.method, CHANGE),
                    change_message=json.dumps(
                        {
                            "source": "dashboard_api",
                            "method": request.method,
                            "action": getattr(self, "action", request.method.lower()),
                            "route": request.resolver_match.url_name
                            if request.resolver_match
                            else None,
                            # Record identifiers, never payloads, notes, tokens or provider data.
                            "targets": {k: str(v) for k, v in kwargs.items()},
                        }
                    ),
                )
            else:
                transaction.set_rollback(True)
            return response
