from __future__ import annotations

from api.rest.dashboard.audit import StaffAuditMixin
from api.rest.dashboard.permissions import ActiveStaff
"""Dashboard view layer for managing remote image promotions."""


import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.rest.dashboard.apps.promotions.serializers import (
    GiffyCallbackDetailSerializer,
    GiffyJobStatusSerializer,
    ImagePromotionSerializer,
    ImagePromotionWriteSerializer,
)
from apps.promotions.client import GiffyClient, GiffyClientError
from apps.promotions.models import BannerSyncStatus, Image
from apps.promotions.signing import (
    CHECKSUM_HEADER,
    CLIENT_HEADER,
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    verify_signed_webhook,
)


def _apply_remote_status(instance: Image, payload: dict) -> None:
    """Persist a remote Giffy job payload into the local promotion record."""
    status_value = payload.get("status", "").lower()
    job_id = payload.get("job_id")
    finished_at = payload.get("finished_at")
    rendered_at = parse_datetime(finished_at) if finished_at else None

    if status_value in {BannerSyncStatus.READY, "success"}:
        instance.mark_banner_ready(
            banner_url=payload.get("result_url") or "",
            job_id=job_id,
            rendered_at=rendered_at,
        )
        return

    if status_value in {BannerSyncStatus.PROCESSING, "pending", BannerSyncStatus.QUEUED}:
        instance.mark_banner_processing()
        return

    if status_value in {BannerSyncStatus.FAILED, "failed"}:
        instance.mark_banner_failed(
            error_message=payload.get("error_message") or "Banner rendering failed.",
            job_id=job_id,
        )


class ImagePromotionViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """CRUD API for image promotions backed by Giffy-generated banner assets."""

    permission_classes = [ActiveStaff]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Image.objects.select_related("podcast").all()

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ImagePromotionWriteSerializer
        return ImagePromotionSerializer

    @action(detail=True, methods=["post"], url_path="refresh-status")
    def refresh_status(self, request, pk=None):
        """Poll Giffy for the latest job state in case a callback was missed."""
        instance = self.get_object()
        if not instance.banner_job_id:
            return Response({"detail": "This promotion has not been submitted to Giffy yet."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            remote_payload = GiffyClient().fetch_banner_job(str(instance.banner_job_id))
        except GiffyClientError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        _apply_remote_status(instance, remote_payload)
        serializer = ImagePromotionSerializer(instance, context=self.get_serializer_context())
        return Response({"promotion": serializer.data, "remote": remote_payload})


class GiffyCallbackAPIView(APIView):
    """Signed callback endpoint used by Giffy to update remote job state."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=GiffyJobStatusSerializer,
        parameters=[
            OpenApiParameter(
                CLIENT_HEADER,
                OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Configured service client identifier.",
            ),
            OpenApiParameter(
                TIMESTAMP_HEADER,
                OpenApiTypes.INT,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Unix timestamp covered by the webhook signature.",
            ),
            OpenApiParameter(
                CHECKSUM_HEADER,
                OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Hex SHA-256 digest of the exact request body.",
            ),
            OpenApiParameter(
                SIGNATURE_HEADER,
                OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="HMAC signature over the canonical webhook request.",
            ),
        ],
        responses={
            200: GiffyCallbackDetailSerializer,
            400: GiffyCallbackDetailSerializer,
            403: GiffyCallbackDetailSerializer,
            404: GiffyCallbackDetailSerializer,
        },
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        if not verify_signed_webhook(
            payload=request.body,
            headers=request.headers,
            secret=settings.GIFFY_SHARED_SECRET,
            expected_client_id=settings.GIFFY_SERVICE_CLIENT_ID,
        ):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_403_FORBIDDEN)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return Response({"detail": "Invalid JSON payload."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = GiffyJobStatusSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        promotion = get_object_or_404(Image.objects.all(), pk=validated["resource_id"])
        _apply_remote_status(promotion, validated)
        return Response({"detail": "Callback processed."}, status=status.HTTP_200_OK)
