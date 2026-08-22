"""HTTP client for coordinating banner generation with the Giffy service."""

from __future__ import annotations

import time
from pathlib import Path

import httpx
from django.conf import settings
from django.urls import reverse

from apps.promotions.models import Image
from apps.promotions.signing import CHECKSUM_HEADER, CLIENT_HEADER, SIGNATURE_HEADER, TIMESTAMP_HEADER, build_upload_signature, sha256_hexdigest


class GiffyClientError(RuntimeError):
    """Raised when the Giffy service cannot accept or return a banner job payload."""


class GiffyClient:
    """Small typed client for the internal Giffy banner-generation service."""

    jobs_path = "/api/banners/jobs"

    def __init__(self):
        self.base_url = getattr(settings, "GIFFY_API_BASE_URL").rstrip("/")
        self.client_id = getattr(settings, "GIFFY_CLIENT_ID")
        self.shared_secret = getattr(settings, "GIFFY_SHARED_SECRET")
        self.timeout = float(getattr(settings, "GIFFY_TIMEOUT_SECONDS"))

    def _callback_url(self, request=None) -> str:
        callback_path = reverse("promotions_dashboard_api:giffy-callback")
        if request is not None:
            return request.build_absolute_uri(callback_path)

        public_base_url = getattr(settings, "MAIN_PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        return f"{public_base_url}{callback_path}"

    def _signed_headers(self, *, method: str, path: str, resource_id: str, checksum: str) -> dict[str, str]:
        timestamp = str(int(time.time()))
        signature = build_upload_signature(
            client_id=self.client_id,
            secret=self.shared_secret,
            method=method,
            path=path,
            timestamp=timestamp,
            resource_id=resource_id,
            checksum=checksum,
        )
        return {
            CLIENT_HEADER: self.client_id,
            TIMESTAMP_HEADER: timestamp,
            CHECKSUM_HEADER: checksum,
            SIGNATURE_HEADER: signature,
        }

    def create_banner_job(self, promotion: Image, *, media_file, logo_file=None, request=None) -> dict:
        """Create a remote banner-render job for the supplied image promotion."""
        media_bytes = media_file.read()
        media_filename = Path(getattr(media_file, "name", "upload.bin")).name
        media_content_type = getattr(media_file, "content_type", "") or "application/octet-stream"

        if not media_bytes:
            raise GiffyClientError("The uploaded promotion file is empty.")

        checksum = sha256_hexdigest(media_bytes)
        headers = self._signed_headers(
            method="POST",
            path=self.jobs_path,
            resource_id=str(promotion.resource_id),
            checksum=checksum,
        )

        data = {
            **promotion.get_banner_payload(),
            "callback_url": self._callback_url(request=request),
            "source_checksum": checksum,
        }
        files = {
            "media": (media_filename, media_bytes, media_content_type),
        }

        logo_filename = ""
        logo_content_type = ""
        if logo_file:
            logo_bytes = logo_file.read()
            if logo_bytes:
                logo_filename = Path(getattr(logo_file, "name", "logo.png")).name
                logo_content_type = getattr(logo_file, "content_type", "") or "image/png"
                files["logo"] = (logo_filename, logo_bytes, logo_content_type)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}{self.jobs_path}", data=data, files=files, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GiffyClientError(f"Unable to submit banner job to Giffy: {exc}") from exc

        payload = response.json()
        if not payload.get("job_id"):
            raise GiffyClientError("Giffy did not return a job identifier.")
        return payload

    def fetch_banner_job(self, job_id: str) -> dict:
        """Fetch the latest job status directly from Giffy."""
        path = f"{self.jobs_path}/{job_id}"
        headers = self._signed_headers(
            method="GET",
            path=path,
            resource_id=job_id,
            checksum=sha256_hexdigest(b""),
        )
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}{path}", headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GiffyClientError(f"Unable to fetch banner job {job_id}: {exc}") from exc
        return response.json()


def submit_image_promotion(promotion: Image, *, media_file, logo_file=None, request=None) -> dict:
    """Submit the promotion to Giffy and persist the queued remote job metadata."""
    payload = GiffyClient().create_banner_job(
        promotion,
        media_file=media_file,
        logo_file=logo_file,
        request=request,
    )
    promotion.mark_banner_submitted(
        job_id=payload["job_id"],
        source_filename=Path(getattr(media_file, "name", "")).name,
        source_content_type=getattr(media_file, "content_type", "") or "application/octet-stream",
    )
    return payload
