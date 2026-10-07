import logging
from datetime import timedelta

from apps.media.audio.models import Audio
from apps.media.delivery import (
    CLOUDFRONT_COOKIE_NAMES,
    HLSDeliveryConfigurationError,
    has_valid_cloudfront_cookies,
    normalize_cached_expiry,
    resolve_hls_cookie_scope,
    resolve_hls_resource_scope,
)
from apps.media.storage import (
    generate_cloudfront_signed_cookies,
    generate_presigned_url_for_name,
)
from apps.memberships.access import AccessService
from apps.memberships.policies import AccessAction, AccessReason
from apps.posts.podcasts.models import Episode
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _get_user_quality(request, default=Audio.Quality.MEDIUM):
    """Resolve desired quality from query param or user's MediaSettings (data-saver)."""
    quality = request.query_params.get("quality")
    if request.user.is_authenticated:
        # lazy import to avoid circular imports at module load
        from apps.media.models import MediaSettings
        try:
            ms = MediaSettings.objects.get(user=request.user)
            if getattr(ms, "data_saver_mode", False):
                return Audio.Quality.LOW
            if not quality:
                return getattr(ms, "streaming_quality", default)
        except Exception:
            pass
    return quality or default


def _url_for_filefield(filefield, expires, *, allow_public_fallback=False):
    """Return an expiring capability, or a public URL only when authorized."""
    if not filefield:
        return None
    storage = getattr(filefield, "storage", default_storage)
    name = filefield.name
    try:
        return generate_presigned_url_for_name(
            storage,
            name,
            expires_in=expires,
            allow_public=allow_public_fallback,
        )
    except Exception:
        return None


def _set_cookies_on_response(
    resp,
    cookies: dict,
    *,
    domain: str,
    path: str,
    expires_at,
):
    """Set cookie dict on DRF Response with consistent attributes."""
    for name in CLOUDFRONT_COOKIE_NAMES:
        resp.set_cookie(
            name,
            cookies[name],
            domain=domain,
            expires=expires_at,
            path=path,
            secure=True,
            httponly=True,
            samesite="None",
        )


def _cloudfront_signed_playlist_response(request, hls, cookie_ttl, cache_margin):
    """
    Return a Response with CloudFront-signed cookies and playlist URL.
    Uses cache to reuse cookies until shortly before expiry.
    """
    if not hls:
        return None, Response({"detail": "HLS not available"}, status=404)

    cloudfront_domain = getattr(settings, "CLOUDFRONT_DOMAIN", None)
    cookie_domain = getattr(settings, "CLOUDFRONT_COOKIE_DOMAIN", None)
    key_pair_id = getattr(settings, "CLOUDFRONT_KEY_PAIR_ID", None)
    private_key_pem = getattr(settings, "CLOUDFRONT_PRIVATE_KEY", None)
    if not (cloudfront_domain and cookie_domain and key_pair_id and private_key_pem):
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)

    try:
        cookie_ttl = int(cookie_ttl)
        cache_margin = int(cache_margin)
        if cookie_ttl <= 0 or cache_margin < 0 or cache_margin >= cookie_ttl:
            raise ValueError
        scope = resolve_hls_cookie_scope(
            delivery_host=cloudfront_domain,
            cookie_domain=cookie_domain,
            request_host=request.get_host(),
        )
    except (HLSDeliveryConfigurationError, ValueError) as exc:
        logger.error("Refusing unusable HLS cookie delivery configuration: %s", exc)
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)

    try:
        resource_scope = resolve_hls_resource_scope(
            prefix=hls.prefix,
            playlist_name=hls.file.name,
        )
    except HLSDeliveryConfigurationError:
        logger.error("Refusing HLS playlist outside its signed resource prefix")
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)

    resource_url = f"https://{scope.delivery_host}/{resource_scope.policy_path}"
    playlist_url = f"https://{scope.delivery_host}/{resource_scope.playlist_path}"
    cache_key = f"cf_signed_cookies:{hls.id}"

    now = timezone.now()
    fresh_after = now + timedelta(seconds=cache_margin)
    try:
        cached = cache.get(cache_key)
    except Exception:
        logger.warning("CloudFront cookie cache read failed; signing freshly")
        cached = None
    if isinstance(cached, dict):
        try:
            expires_at = normalize_cached_expiry(cached.get("expires_at"))
            cookies = cached.get("cookies")
            cache_matches = (
                cached.get("schema_version") == 2
                and cached.get("resource_url") == resource_url
            )
        except Exception:
            expires_at = None
            cookies = None
            cache_matches = False
        if (
            cache_matches
            and expires_at is not None
            and fresh_after < expires_at <= now + timedelta(seconds=cookie_ttl + 5)
            and has_valid_cloudfront_cookies(
                cookies,
                expected_key_pair_id=key_pair_id,
            )
        ):
            resp = Response(
                {
                    "playlist_url": playlist_url,
                    "expires_at": expires_at.isoformat(),
                }
            )
            _set_cookies_on_response(
                resp,
                cookies,
                domain=scope.cookie_domain,
                path=resource_scope.cookie_path,
                expires_at=expires_at,
            )
            return resp, None

    # generate new cookies
    try:
        signed = generate_cloudfront_signed_cookies(
            resource_url,
            key_pair_id,
            private_key_pem,
            expires_in_seconds=cookie_ttl,
        )
    except Exception:
        logger.exception(
            "Failed to generate CloudFront cookies for hls=%s",
            getattr(hls, "id", "<nil>"),
        )
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)

    if not isinstance(signed, dict):
        logger.error("CloudFront signer returned a non-dictionary result")
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)
    try:
        cookies = signed.get("cookies")
        expires_at = normalize_cached_expiry(signed.get("expires_at"))
    except Exception:
        cookies = None
        expires_at = None
    if (
        not has_valid_cloudfront_cookies(
            cookies,
            expected_key_pair_id=key_pair_id,
        )
        or expires_at is None
        or expires_at <= fresh_after
        or expires_at > now + timedelta(seconds=cookie_ttl + 5)
    ):
        logger.error("CloudFront signer returned incomplete cookies or an invalid expiry")
        return None, Response({"detail": "HLS delivery is unavailable"}, status=503)

    ttl_seconds = int((expires_at - now).total_seconds()) - cache_margin
    try:
        cache.set(
            cache_key,
            {
                "schema_version": 2,
                "resource_url": resource_url,
                "cookies": cookies,
                "expires_at": expires_at,
            },
            timeout=ttl_seconds,
        )
    except Exception:
        logger.warning(
            "CloudFront cookie cache write failed; returning fresh credentials"
        )

    resp = Response(
        {"playlist_url": playlist_url, "expires_at": expires_at.isoformat()}
    )
    _set_cookies_on_response(
        resp,
        cookies,
        domain=scope.cookie_domain,
        path=resource_scope.cookie_path,
        expires_at=expires_at,
    )
    return resp, None


def user_has_access_to_episode(user, episode: Episode):
    """
    Return one of: "full", "preview".
    Uses AccessService implementation for membership checks.
    """
    decision = AccessService.get_instance().evaluate(
        user=user,
        resource=episode,
        action=AccessAction.STREAM,
    )
    return "full" if decision.allowed else "preview"


@extend_schema(
    parameters=[
        OpenApiParameter("quality", OpenApiTypes.STR, description="low, medium, or high"),
        OpenApiParameter("format", OpenApiTypes.STR, description="progressive or hls"),
    ],
    responses={
        200: OpenApiResponse(description="Expiring full/preview URL or HLS credential"),
        403: OpenApiResponse(description="Full media denied and no permitted fallback"),
        404: OpenApiResponse(description="Episode or requested media variant not found"),
        503: OpenApiResponse(description="An expiring media capability could not be issued"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def stream_episode_progressive(request, episode_id):
    """
    Unified endpoint for progressive and HLS streaming.
    GET /api/episodes/<id>/stream/?quality=medium&format=hls
    """
    episode = get_object_or_404(Episode, pk=episode_id)
    fmt = request.query_params.get("format", "progressive").lower()
    quality = _get_user_quality(request)

    decision = AccessService.get_instance().evaluate(
        user=request.user,
        resource=episode,
        action=AccessAction.STREAM,
    )

    # HLS branch
    if fmt == "hls":
        # find HLS record (ensure your model provides prefix/file fields)
        hls = episode.audio_qs.filter(quality=Audio.Quality.HLS).first()
        if not decision.allowed:
            return Response(
                {
                    "detail": "HLS playback requires full access",
                    "reason": decision.reason.value,
                },
                status=403,
            )

        cookie_ttl = getattr(settings, "CLOUDFRONT_COOKIE_TTL", 900)
        cache_margin = getattr(settings, "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN", 60)
        resp, err = _cloudfront_signed_playlist_response(
            request,
            hls,
            cookie_ttl,
            cache_margin,
        )
        if err:
            return err
        return resp

    # Preview branch
    if not decision.allowed:
        if not decision.preview_allowed:
            return Response(
                {
                    "detail": "Preview not available",
                    "reason": decision.reason.value,
                },
                status=403,
            )
        preview_audio = episode.audio_qs.filter(quality="preview").first()
        if not preview_audio:
            return Response(
                {
                    "detail": "Preview not available",
                    "reason": decision.reason.value,
                },
                status=403,
            )
        url = _url_for_filefield(
            preview_audio.file,
            expires=getattr(settings, "PRESIGN_PREVIEW_EXPIRES_SECONDS", 600),
        )
        if not url:
            return Response({"detail": "Could not generate preview URL"}, status=503)
        return Response({"url": url, "type": "preview"})

    # Full progressive branch
    audio = episode.audio_qs.filter(quality=quality).first()
    if not audio:
        # fallback order
        audio = (episode.audio_qs.filter(quality=Audio.Quality.MEDIUM).first()
                 or episode.audio_qs.filter(quality=Audio.Quality.HIGH).first()
                 or episode.audio_qs.master(episode_id=episode_id))
    if not audio:
        return Response({"detail": "No audio variant available"}, status=404)

    url = _url_for_filefield(
        audio.file,
        expires=getattr(settings, "PRESIGN_EXPIRES_SECONDS", 3600),
        allow_public_fallback=decision.reason == AccessReason.PUBLIC,
    )
    if not url:
        return Response({"detail": "Could not generate URL"}, status=503)
    return Response({"url": url, "type": "full", "quality": audio.quality})
