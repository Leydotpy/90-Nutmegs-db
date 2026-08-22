import logging

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.media.audio.models import Audio
from apps.media.storage import generate_cloudfront_signed_cookies
from apps.media.storage import generate_presigned_url_for_name
from apps.memberships.access import AccessService
from apps.posts.podcasts.models import Episode

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


def _url_for_filefield(filefield, expires):
    """Return presigned URL if possible, otherwise storage.url or None."""
    if not filefield:
        return None
    storage = getattr(filefield, "storage", default_storage)
    name = filefield.name
    try:
        return generate_presigned_url_for_name(storage, name, expires_in=expires)
    except Exception:
        # fallback to storage.url (may be None or public)
        try:
            return storage.url(name)
        except Exception:
            return None


def _set_cookies_on_response(resp, cookies: dict):
    """Set cookie dict on DRF Response with consistent attributes."""
    for name, val in (cookies or {}).items():
        resp.set_cookie(name, val, secure=True, httponly=False, samesite="None")


def _cloudfront_signed_playlist_response(hls, cookie_ttl, cache_margin):
    """
    Return a Response with CloudFront-signed cookies and playlist URL.
    Uses cache to reuse cookies until shortly before expiry.
    """
    if not hls:
        return None, Response({"detail": "HLS not available"}, status=404)

    cloudfront_domain = getattr(settings, "CLOUDFRONT_DOMAIN", None)
    key_pair_id = getattr(settings, "CLOUDFRONT_KEY_PAIR_ID", None)
    private_key_pem = getattr(settings, "CLOUDFRONT_PRIVATE_KEY", None)
    if not (cloudfront_domain and key_pair_id and private_key_pem):
        return None, Response({"detail": "CloudFront signing is not configured"}, status=500)

    resource_url = f"https://{cloudfront_domain}/{hls.prefix}/*"
    cache_key = f"cf_signed_cookies:{hls.id}"

    cached = cache.get(cache_key)
    now = timezone.now()
    if cached:
        expires_at = cached.get("expires_at")
        if expires_at and expires_at > now:
            resp = Response({"playlist_url": f"https://{cloudfront_domain}/{hls.file.name}",
                             "expires_at": expires_at.isoformat()})
            _set_cookies_on_response(resp, cached.get("cookies", {}))
            return resp, None

    # generate new cookies
    try:
        signed = generate_cloudfront_signed_cookies(resource_url, key_pair_id, private_key_pem,
                                                    expires_in_seconds=cookie_ttl)
    except Exception as exc:
        logger.exception("Failed to generate CloudFront cookies for hls=%s: %s", getattr(hls, "id", "<nil>"), exc)
        return None, Response({"detail": "Failed to sign CloudFront cookies"}, status=500)

    cookies = signed.get("cookies", {})
    expires_at = signed.get("expires_at")
    ttl_seconds = int((expires_at - now).total_seconds()) - cache_margin
    if ttl_seconds < 1:
        ttl_seconds = max(1, int(cookie_ttl / 2))
    cache.set(cache_key, {"cookies": cookies, "expires_at": expires_at}, timeout=ttl_seconds)

    resp = Response(
        {"playlist_url": f"https://{cloudfront_domain}/{hls.file.name}", "expires_at": expires_at.isoformat()})
    _set_cookies_on_response(resp, cookies)
    return resp, None


def user_has_access_to_episode(user, episode: Episode):
    """
    Return one of: "full", "preview".
    Uses AccessService implementation for membership checks.
    """
    has_access = AccessService.get_instance().has_access(user, episode)
    return "full" if has_access else "preview"


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

    access = user_has_access_to_episode(request.user, episode)

    # HLS branch
    if fmt == "hls":
        # find HLS record (ensure your model provides prefix/file fields)
        hls = episode.audio_qs.filter(quality=Audio.Quality.HLS).first()
        if access == "preview":
            return Response({"detail": "HLS playback requires full access"}, status=403)

        cookie_ttl = getattr(settings, "CLOUDFRONT_COOKIE_TTL", 900)
        cache_margin = getattr(settings, "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN", 60)
        resp, err = _cloudfront_signed_playlist_response(hls, cookie_ttl, cache_margin)
        if err:
            return err
        return resp

    # Preview branch
    if access == "preview":
        preview_audio = episode.audio_qs.filter(quality="preview").first()
        if not preview_audio:
            return Response({"detail": "Preview not available"}, status=403)
        url = _url_for_filefield(preview_audio.file, expires=getattr(settings, "PRESIGN_PREVIEW_EXPIRES_SECONDS", 600))
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

    url = _url_for_filefield(audio.file, expires=getattr(settings, "PRESIGN_EXPIRES_SECONDS", 3600))
    if not url:
        return Response({"detail": "Could not generate URL"}, status=503)
    return Response({"url": url, "type": "full", "quality": audio.quality})
