import datetime
from unittest import mock

from apps.category.models import Category
from apps.media.audio.models import Audio
from apps.media.storage import generate_presigned_url_for_name
from apps.memberships.access import AccessService
from apps.memberships.models import Entitlement, Plan
from apps.posts.podcasts.models import Episode, Podcast
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from api.rest.web.apps.media.streaming.views import stream_episode_progressive

VALID_CLOUDFRONT_COOKIES = {
    "CloudFront-Key-Pair-Id": "test-key",
    "CloudFront-Policy": "signed-policy",
    "CloudFront-Signature": "signed-signature",
}
VALID_HLS_SETTINGS = {
    "ALLOWED_HOSTS": ["api.example.test", "api.other.test", "testserver"],
    "CLOUDFRONT_DOMAIN": "media.example.test",
    "CLOUDFRONT_COOKIE_DOMAIN": "example.test",
    "CLOUDFRONT_KEY_PAIR_ID": "test-key",
    "CLOUDFRONT_PRIVATE_KEY": "test-private-key",
}


class EpisodeStreamingAuthorizationTests(TestCase):
    def setUp(self):
        cache.clear()
        AccessService._instance = None
        self.factory = APIRequestFactory()
        self.now = timezone.now()
        self.podcast = Podcast.objects.create(
            title="Streaming tests",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        self.fan = Plan.objects.create(name="Fan", tier=Plan.Level.FAN)

    def episode(self, *, public=True, preview=False, full=True, hls=False):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title=f"Stream {Episode.objects.count() + 1}",
            public_release_date=self.now - datetime.timedelta(hours=1),
            exclusive=not public,
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=(Episode.Visibility.PUBLIC if public else Episode.Visibility.PLAN),
            premium_available_at=self.now - datetime.timedelta(hours=1),
            public_available_at=(self.now - datetime.timedelta(hours=1) if public else None),
            required_plan=None if public else self.fan,
        )
        if not public:
            category = Category.objects.create(
                name=f"Premium {Category.objects.count() + 1}",
                tier=self.fan,
            )
            episode.categories.add(category)
        if full:
            Audio.objects.create(
                episode=episode,
                name="Medium",
                quality=Audio.Quality.MEDIUM,
                file=f"episodes/{episode.pk}/medium.mp3",
            )
        if preview:
            Audio.objects.create(
                episode=episode,
                name="Preview",
                quality=Audio.Quality.PREVIEW,
                file=f"episodes/{episode.pk}/preview.mp3",
            )
        if hls:
            prefix = f"episodes/{episode.pk}/hls"
            Audio.objects.create(
                episode=episode,
                name="HLS",
                quality=Audio.Quality.HLS,
                file=f"{prefix}/playlist.m3u8",
                prefix=prefix,
            )
        return episode

    def get(self, episode, query="", *, user=None, host="testserver"):
        request = self.factory.get(
            f"/episodes/{episode.pk}/stream/{query}",
            HTTP_HOST=host,
        )
        if user is not None:
            force_authenticate(request, user=user)
        return stream_episode_progressive(request, episode_id=episode.pk)

    def hls_audio(self, episode):
        return episode.audio_qs.get(quality=Audio.Quality.HLS)

    @mock.patch(
        "api.rest.web.apps.media.streaming.views.generate_presigned_url_for_name",
        return_value="https://cdn.example.test/full.mp3?signature=short-lived",
    )
    def test_public_full_stream_preserves_contract(self, sign_url):
        episode = self.episode(public=True)

        response = self.get(episode)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "full")
        self.assertIn("url", response.data)
        self.assertTrue(sign_url.call_args.kwargs["allow_public"])

    @mock.patch(
        "api.rest.web.apps.media.streaming.views.generate_presigned_url_for_name",
        return_value="https://cdn.example.test/preview.mp3?signature=short-lived",
    )
    def test_anonymous_premium_listener_receives_only_preview(self, sign_url):
        episode = self.episode(public=False, preview=True)

        response = self.get(episode)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "preview")
        self.assertNotIn("quality", response.data)
        self.assertFalse(sign_url.call_args.kwargs["allow_public"])

    def test_denial_never_returns_full_url_when_preview_is_unavailable(self):
        episode = self.episode(public=False, preview=False, full=True)

        response = self.get(episode)

        self.assertEqual(response.status_code, 403, response.data)
        self.assertNotIn("url", response.data)
        self.assertEqual(response.data["reason"], "requires_login")

    def test_preview_only_listener_cannot_receive_hls_credentials(self):
        episode = self.episode(public=False, preview=True, hls=True)

        response = self.get(episode, "?format=hls")

        self.assertEqual(response.status_code, 403, response.data)
        self.assertNotIn("playlist_url", response.data)

    @mock.patch(
        "api.rest.web.apps.media.streaming.views.generate_presigned_url_for_name",
        return_value="https://cdn.example.test/full.mp3?signature=short-lived",
    )
    def test_direct_entitlement_issues_protected_full_capability(self, sign_url):
        episode = self.episode(public=False, preview=True)
        user = get_user_model().objects.create(
            username="entitled",
            clerk_user_id="clerk_entitled",
        )
        Entitlement.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(episode),
            object_id=str(episode.pk),
        )

        response = self.get(episode, user=user)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["type"], "full")
        self.assertFalse(sign_url.call_args.kwargs["allow_public"])

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_authorized_hls_cookie_is_short_lived_and_http_only(self, sign_cookies):
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": expires_at,
        }
        episode = self.episode(public=True, hls=True)

        response = self.get(
            episode,
            "?format=hls",
            host="api.example.test",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["playlist_url"],
            f"https://media.example.test/episodes/{episode.pk}/hls/playlist.m3u8",
        )
        self.assertEqual(
            sign_cookies.call_args.args[0],
            f"https://media.example.test/episodes/{episode.pk}/hls/*",
        )
        policy_cookie = response.cookies["CloudFront-Policy"]
        self.assertTrue(policy_cookie["httponly"])
        self.assertTrue(policy_cookie["secure"])
        self.assertEqual(policy_cookie["samesite"], "None")
        self.assertEqual(policy_cookie["domain"], "example.test")
        self.assertEqual(
            policy_cookie["path"],
            f"/episodes/{episode.pk}/hls/",
        )
        self.assertTrue(policy_cookie["expires"])
        self.assertEqual(response.data["expires_at"], expires_at.isoformat())

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_simultaneous_episode_cookies_use_distinct_prefix_paths(self, sign_cookies):
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": expires_at,
        }
        first_episode = self.episode(public=True, hls=True)
        second_episode = self.episode(public=True, hls=True)

        first_response = self.get(
            first_episode,
            "?format=hls",
            host="api.example.test",
        )
        second_response = self.get(
            second_episode,
            "?format=hls",
            host="api.example.test",
        )

        self.assertEqual(first_response.status_code, 200, first_response.data)
        self.assertEqual(second_response.status_code, 200, second_response.data)
        first_path = first_response.cookies["CloudFront-Policy"]["path"]
        second_path = second_response.cookies["CloudFront-Policy"]["path"]
        self.assertEqual(first_path, f"/episodes/{first_episode.pk}/hls/")
        self.assertEqual(second_path, f"/episodes/{second_episode.pk}/hls/")
        self.assertNotEqual(first_path, second_path)

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_naive_cached_hls_expiry_is_normalized_before_comparison(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        hls = self.hls_audio(episode)
        naive_expiry = (timezone.now() + datetime.timedelta(minutes=10)).replace(tzinfo=None)
        resource_url = f"https://media.example.test/{hls.prefix}/*"
        cache.set(
            f"cf_signed_cookies:{hls.id}",
            {
                "schema_version": 2,
                "resource_url": resource_url,
                "cookies": VALID_CLOUDFRONT_COOKIES,
                "expires_at": naive_expiry,
            },
        )

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 200, response.data)
        normalized = datetime.datetime.fromisoformat(response.data["expires_at"])
        self.assertTrue(timezone.is_aware(normalized))
        self.assertEqual(response.cookies["CloudFront-Policy"]["domain"], "example.test")
        self.assertEqual(
            response.cookies["CloudFront-Policy"]["path"],
            f"/episodes/{episode.pk}/hls/",
        )
        sign_cookies.assert_not_called()

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_legacy_naive_cache_shape_is_a_safe_miss(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        hls = self.hls_audio(episode)
        cache.set(
            f"cf_signed_cookies:{hls.id}",
            {
                "cookies": VALID_CLOUDFRONT_COOKIES,
                "expires_at": (timezone.now() + datetime.timedelta(minutes=10)).replace(
                    tzinfo=None
                ),
            },
        )
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": expires_at,
        }

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 200, response.data)
        sign_cookies.assert_called_once()
        refreshed = cache.get(f"cf_signed_cookies:{hls.id}")
        self.assertEqual(refreshed["schema_version"], 2)
        self.assertTrue(timezone.is_aware(refreshed["expires_at"]))

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_invalid_cached_hls_expiry_is_a_miss_and_is_replaced(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        hls = self.hls_audio(episode)
        resource_url = f"https://media.example.test/{hls.prefix}/*"
        cache.set(
            f"cf_signed_cookies:{hls.id}",
            {
                "schema_version": 2,
                "resource_url": resource_url,
                "cookies": VALID_CLOUDFRONT_COOKIES,
                "expires_at": "not-a-datetime",
            },
        )
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": expires_at,
        }

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 200, response.data)
        sign_cookies.assert_called_once()
        refreshed = cache.get(f"cf_signed_cookies:{hls.id}")
        self.assertEqual(refreshed["resource_url"], resource_url)
        self.assertEqual(refreshed["expires_at"], expires_at)

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_cache_read_outage_signs_fresh_credentials(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": expires_at,
        }
        original_get = cache.get

        def fail_hls_cache_read(key, *args, **kwargs):
            if str(key).startswith("cf_signed_cookies:"):
                raise RuntimeError("cache unavailable")
            return original_get(key, *args, **kwargs)

        with mock.patch.object(cache, "get", side_effect=fail_hls_cache_read):
            response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 200, response.data)
        sign_cookies.assert_called_once()

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_cache_write_outage_still_returns_fresh_credentials(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": timezone.now() + datetime.timedelta(minutes=10),
        }
        original_set = cache.set

        def fail_hls_cache_write(key, *args, **kwargs):
            if str(key).startswith("cf_signed_cookies:"):
                raise RuntimeError("cache unavailable")
            return original_set(key, *args, **kwargs)

        with mock.patch.object(cache, "set", side_effect=fail_hls_cache_write):
            response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.cookies["CloudFront-Policy"]["domain"], "example.test")

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_incomplete_signer_output_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        sign_cookies.return_value = {
            "cookies": {"CloudFront-Policy": "only-one-cookie"},
            "expires_at": timezone.now() + datetime.timedelta(minutes=10),
        }

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_signer_expiry_beyond_configured_ttl_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        sign_cookies.return_value = {
            "cookies": VALID_CLOUDFRONT_COOKIES,
            "expires_at": timezone.now() + datetime.timedelta(days=1),
        }

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_api_host_outside_cookie_domain_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)

        response = self.get(episode, "?format=hls", host="api.other.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)
        sign_cookies.assert_not_called()

    @override_settings(
        **{
            **VALID_HLS_SETTINGS,
            "CLOUDFRONT_DOMAIN": "d111111abcdef8.cloudfront.net",
        }
    )
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_unrelated_cloudfront_delivery_host_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)
        sign_cookies.assert_not_called()

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_playlist_outside_signed_prefix_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        hls = self.hls_audio(episode)
        hls.file.name = f"episodes/{episode.pk}/hls-other/playlist.m3u8"
        hls.save(update_fields=["file"])

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)
        sign_cookies.assert_not_called()

    @override_settings(**VALID_HLS_SETTINGS)
    @mock.patch("api.rest.web.apps.media.streaming.views.generate_cloudfront_signed_cookies")
    def test_playlist_traversal_under_signed_prefix_fails_closed(self, sign_cookies):
        episode = self.episode(public=True, hls=True)
        hls = self.hls_audio(episode)
        hls.file.name = f"{hls.prefix}/../private/playlist.m3u8"
        hls.save(update_fields=["file"])

        response = self.get(episode, "?format=hls", host="api.example.test")

        self.assertEqual(response.status_code, 503, response.data)
        self.assertNotIn("playlist_url", response.data)
        self.assertFalse(response.cookies)
        sign_cookies.assert_not_called()


class StorageCapabilityTests(TestCase):
    class PublicOnlyStorage:
        def url(self, name):
            return f"https://public.example.test/{name}"

    def test_queryless_storage_url_fails_closed_for_protected_object(self):
        storage = self.PublicOnlyStorage()

        self.assertIsNone(generate_presigned_url_for_name(storage, "private/audio.mp3"))
        self.assertEqual(
            generate_presigned_url_for_name(
                storage,
                "public/audio.mp3",
                allow_public=True,
            ),
            "https://public.example.test/public/audio.mp3",
        )

    def test_arbitrary_query_does_not_make_a_public_url_a_capability(self):
        class TrackingStorage:
            def url(self, name):
                return f"https://public.example.test/{name}?campaign=listener"

        storage = TrackingStorage()

        self.assertIsNone(generate_presigned_url_for_name(storage, "private/audio.mp3"))
        self.assertEqual(
            generate_presigned_url_for_name(
                storage,
                "public/audio.mp3",
                allow_public=True,
            ),
            "https://public.example.test/public/audio.mp3?campaign=listener",
        )

    def test_known_expiring_storage_signature_is_accepted(self):
        class SignedStorage:
            def url(self, name):
                return (
                    f"https://private.example.test/{name}"
                    "?X-Amz-Expires=300&X-Amz-Signature=test-signature"
                )

        expected = (
            "https://private.example.test/private/audio.mp3"
            "?X-Amz-Expires=300&X-Amz-Signature=test-signature"
        )

        self.assertEqual(
            generate_presigned_url_for_name(
                SignedStorage(),
                "private/audio.mp3",
            ),
            expected,
        )

    def test_mismatched_signature_contract_fails_closed(self):
        class MismatchedStorage:
            def url(self, name):
                return (
                    f"https://private.example.test/{name}"
                    "?X-Amz-Signature=test-signature&se=2099-01-01"
                )

        self.assertIsNone(
            generate_presigned_url_for_name(
                MismatchedStorage(),
                "private/audio.mp3",
            )
        )
