import logging
import os
import shutil
import tempfile
from datetime import timedelta

from celery import Task, shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.media.audio.models import Audio
from apps.media.delivery import (
    HLSDeliveryConfigurationError,
    has_valid_cloudfront_cookies,
    normalize_cached_expiry,
    resolve_hls_cookie_scope,
    resolve_hls_resource_scope,
)
from apps.media.storage import generate_cloudfront_signed_cookies
from apps.media.utils import detect_master_audio_info

from .utils import (
    generate_hls_stream,
    generate_preview_clip,
    generate_transcription,
    generate_variants,
)

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5, "countdown": 10}
    retry_backoff = True
    acks_late = True


@shared_task(base=BaseTaskWithRetry, bind=True, name="CloudFront Audio HLS Signing Task")
def rotate_cloud_front_cookies(_self):
    """
    Iterate HLSStream rows and ensure cached CloudFront signed cookies exist for each prefix.
    This pre-warms/rotates cookies so the API endpoint can quickly return them without
    generating them on-demand repeatedly.
    """
    domain = getattr(settings, "CLOUDFRONT_DOMAIN", None)
    cookie_domain = getattr(settings, "CLOUDFRONT_COOKIE_DOMAIN", None)
    key_pair_id = getattr(settings, "CLOUDFRONT_KEY_PAIR_ID", None)
    private_key_pem = getattr(settings, "CLOUDFRONT_PRIVATE_KEY", None)
    cookie_ttl = getattr(settings, "CLOUDFRONT_COOKIE_TTL", 900)
    cache_margin = getattr(settings, "CLOUDFRONT_SIGN_CACHE_TIMEOUT_MARGIN", 60)

    if not domain or not cookie_domain or not key_pair_id or not private_key_pem:
        logger.warning("CloudFront signing not configured; rotate_cloudfront_cookies will not run")
        return

    try:
        cookie_ttl = int(cookie_ttl)
        cache_margin = int(cache_margin)
        if cookie_ttl <= 0 or cache_margin < 0 or cache_margin >= cookie_ttl:
            raise ValueError
        scope = resolve_hls_cookie_scope(
            delivery_host=domain,
            cookie_domain=cookie_domain,
        )
    except (HLSDeliveryConfigurationError, ValueError) as exc:
        logger.warning("CloudFront HLS delivery configuration is invalid: %s", exc)
        return

    streams = Audio.objects.filter(quality=Audio.Quality.HLS).values(
        "id",
        "prefix",
        "file",
    )
    for s in streams:
        hls_id = s["id"]
        prefix = s["prefix"]
        try:
            resource_scope = resolve_hls_resource_scope(
                prefix=prefix,
                playlist_name=s["file"],
            )
        except HLSDeliveryConfigurationError:
            logger.warning(
                "Skipping CloudFront rotation for an HLS playlist outside its prefix"
            )
            continue
        resource_url = f"https://{scope.delivery_host}/{resource_scope.policy_path}"
        cache_key = f"cf_signed_cookies:{hls_id}"
        try:
            cached = cache.get(cache_key)
        except Exception:
            logger.warning("CloudFront cookie cache read failed; rotating freshly")
            cached = None
        needs_refresh = True
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
            now = timezone.now()
            if (
                cache_matches
                and has_valid_cloudfront_cookies(
                    cookies,
                    expected_key_pair_id=key_pair_id,
                )
                and expires_at is not None
                and expires_at > now + timedelta(seconds=cache_margin)
                and expires_at <= now + timedelta(seconds=cookie_ttl + 5)
            ):
                needs_refresh = False

        if not needs_refresh:
            continue

        try:
            signed = generate_cloudfront_signed_cookies(
                resource_url,
                key_pair_id,
                private_key_pem,
                expires_in_seconds=cookie_ttl,
            )
            if not isinstance(signed, dict):
                raise TypeError("CloudFront signer returned a non-dictionary result")
            cookies = signed.get("cookies")
            expires_at = normalize_cached_expiry(signed.get("expires_at"))
            now = timezone.now()
            if (
                not has_valid_cloudfront_cookies(
                    cookies,
                    expected_key_pair_id=key_pair_id,
                )
                or expires_at is None
                or expires_at <= now + timedelta(seconds=cache_margin)
                or expires_at > now + timedelta(seconds=cookie_ttl + 5)
            ):
                raise ValueError(
                    "CloudFront signer returned incomplete cookies or an invalid expiry"
                )
            ttl_seconds = int(
                (expires_at - now).total_seconds()
            ) - cache_margin
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
                logger.warning("CloudFront cookie cache write failed")
            logger.info("Rotated CloudFront cookies for hls_id=%s prefix=%s", hls_id, prefix)
        except Exception:
            logger.exception(
                "Failed rotating CloudFront cookies for hls_id=%s prefix=%s",
                hls_id,
                prefix,
            )


@shared_task(base=BaseTaskWithRetry, bind=True, name="Audio Processing Pipeline")
def process_audio(
        _self,
        audio_id: str,
        user_id: int | None = None,
        provider: str = "openai",
        provider_options: dict | None = None,
        *,
        generate_variants_flag: bool = True,
        generate_hls_flag: bool = True,
        generate_preview_flag: bool = True,
        generate_transcription_flag: bool = True,
        generate_chapters_flag: bool = True,
        generate_summary_flag: bool = True,
):
    provider_options = provider_options or {}
    tmpdir = tempfile.mkdtemp(prefix=f"ep-job-{audio_id}-")

    try:
        audio = Audio.objects.select_related("episode").get(id=audio_id)
    except Audio.DoesNotExist:
        logger.exception(f"Audio {audio_id} not found")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    episode = audio.episode
    storage_base = episode.slug

    try:
        # download master locally
        master_local = os.path.join(tmpdir, "master")
        with open(master_local, "wb") as fh:
            for chunk in audio.file.chunks():
                fh.write(chunk)

        # Update master metadata
        info = detect_master_audio_info(master_local)
        audio.name = info.get("title")
        audio.bitrate = info.get("bitrate_kbps")
        audio.sample_rate = info.get("sample_rate")
        audio.codec = info.get("codec")
        audio.duration = int(info.get("duration", 0))
        audio.save(update_fields=["name", "bitrate", "sample_rate", "codec", "duration"])

        # Variants
        if generate_variants_flag:
            generate_variants(master_local, episode, storage_base)

        if generate_hls_flag:
            # create hls stream (uploads to storage and returns HLSStream)
            generate_hls_stream(master_local, episode, storage_base, preset_key="medium", segment_time=10)

        # Preview
        if generate_preview_flag:
            generate_preview_clip(master_local, episode, storage_base)

        # Transcription (optional)
        if generate_transcription_flag:
            try:
                generate_transcription(
                    tmpdir=tmpdir,
                    user_id=user_id,
                    provider=provider,
                    provider_options=provider_options,
                    master_local=master_local,
                    episode=episode,
                    storage_base=storage_base,
                    generate_chapters=generate_chapters_flag,
                    generate_summary=generate_summary_flag,
                )
            except Exception as e:
                logger.exception("Transcription generation failed", exc_info=e)
                pass
        # done
        # If HLSStream exists we already created/updated it in generate_hls_stream
        audio.processed = True
        audio.save(update_fields=["processed"])
        return audio.id
    finally:
        # always cleanup tempdir
        shutil.rmtree(tmpdir, ignore_errors=True)
