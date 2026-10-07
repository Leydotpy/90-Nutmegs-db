"""Provider contract tests against injected pycflare-facing fakes."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from unittest import mock

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from pycflare.exceptions import TransportError
from pycflare.media import ImagesDirectUpload, StreamDirectUpload, TusUploadSession
from pycflare.models import TemporaryURL
from pycflare.storage import R2Object, R2Settings

from apps.media.providers.cloudflare import (
    CloudflareImagePlatform,
    CloudflareObjectStorage,
    CloudflareVideoPlatform,
)
from apps.media.providers.config import CloudflareMediaConfig
from apps.media.providers.contracts import MediaProviderError, UploadIntent

NOW = datetime(2026, 8, 28, 12, tzinfo=UTC)
TEST_STREAM_PRIVATE_KEY_B64 = base64.b64encode(
    rsa.generate_private_key(public_exponent=65_537, key_size=2048).private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption(),
    )
).decode("ascii")


def valid_config(**overrides):
    values = {
        "account_id": "account-id",
        "api_token": "api-token",
        "r2_access_key_id": "r2-access-key",
        "r2_secret_access_key": "r2-secret",
        "r2_private_bucket_name": "sanfootball-private-media",
        "r2_public_bucket_name": "sanfootball-public-media",
        "r2_public_base_url": "https://media.example.test",
        "images_account_hash": "images-hash",
        "images_signing_key": "images-signing-key",
        "stream_customer_code": "stream-code",
        "stream_signing_key_id": "stream-key-id",
        "stream_signing_private_key_b64": TEST_STREAM_PRIVATE_KEY_B64,
        "stream_webhook_secret": "webhook-secret",
        "stream_allowed_origins": ("app.example.test",),
    }
    values.update(overrides)
    return CloudflareMediaConfig(**values)


class ContractRedactionTests(SimpleTestCase):
    def test_upload_capability_is_not_in_repr(self):
        intent = UploadIntent(
            provider="cloudflare",
            product="r2",
            resource_id="temporary/uploads/asset",
            upload_url="https://secret.example.test/?signature=bearer",
            headers={"Authorization": "secret"},
        )

        rendered = repr(intent)

        self.assertNotIn("signature", rendered)
        self.assertNotIn("Authorization", rendered)
        self.assertIn("temporary/uploads/asset", rendered)

    def test_configuration_repr_redacts_every_secret(self):
        rendered = repr(valid_config())

        for secret in (
            "api-token",
            "r2-access-key",
            "r2-secret",
            "images-signing-key",
            TEST_STREAM_PRIVATE_KEY_B64,
            "webhook-secret",
        ):
            self.assertNotIn(secret, rendered)

    def test_production_public_r2_origin_rejects_r2_dev(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "not r2.dev"):
            valid_config(r2_public_base_url="https://pub-test.r2.dev")

    def test_shared_upload_ttl_respects_cloudflare_images_bounds(self):
        for invalid_ttl in (119, 21_601):
            with self.subTest(invalid_ttl=invalid_ttl), self.assertRaises(ImproperlyConfigured):
                valid_config(upload_url_ttl_seconds=invalid_ttl)

        self.assertEqual(valid_config(upload_url_ttl_seconds=120).upload_url_ttl_seconds, 120)
        self.assertEqual(
            valid_config(upload_url_ttl_seconds=21_600).upload_url_ttl_seconds,
            21_600,
        )

    def test_stream_origins_are_playback_hostnames_not_urls(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "without a scheme"):
            valid_config(stream_allowed_origins=("https://app.example.test",))

    def test_stream_signing_key_must_be_an_rsa_pem(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "PEM private key"):
            valid_config(
                stream_signing_private_key_b64=base64.b64encode(b"not-a-key").decode("ascii")
            )


class R2AdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = mock.Mock()
        self.client.settings = R2Settings(
            account_id="account-id",
            access_key_id="access",
            secret_access_key="secret",
            bucket_name="media",
        )
        self.adapter = CloudflareObjectStorage(self.client)

    def test_upload_intent_scopes_method_key_type_and_expiry(self):
        expires_at = NOW + timedelta(minutes=10)
        self.client.presign_put.return_value = TemporaryURL(
            "https://r2.example.test/?signed=upload",
            expires_at,
        )

        intent = self.adapter.create_upload_intent(
            key="temporary/uploads/opaque.mp3",
            content_type="audio/mpeg",
            expires_in=600,
        )

        self.client.presign_put.assert_called_once_with(
            "temporary/uploads/opaque.mp3",
            expires_in=600,
            content_type="audio/mpeg",
        )
        self.assertEqual(intent.method, "PUT")
        self.assertEqual(intent.headers, {"Content-Type": "audio/mpeg"})
        self.assertEqual(intent.expires_at, expires_at)

    def test_head_does_not_treat_uploader_metadata_as_a_trusted_checksum(self):
        self.client.head.return_value = R2Object(
            key="published/audio/opaque.mp3",
            size=42,
            etag="etag",
            content_type="audio/mpeg",
            metadata={"sha256": "abc"},
        )

        result = self.adapter.head(key="published/audio/opaque.mp3")

        self.assertEqual(result.byte_size, 42)
        self.assertIsNone(result.checksum)
        self.assertEqual(result.metadata["sha256"], "abc")

    def test_promotion_conditionally_copies_then_heads_canonical_object(self):
        self.client.head.return_value = R2Object(
            key="canonical/audio/asset/object.mp3",
            size=42,
            etag="destination-etag",
            content_type="audio/mpeg",
        )

        result = self.adapter.promote(
            source_container="private-media",
            source_key="temporary/uploads/asset/session.mp3",
            destination_key="canonical/audio/asset/object.mp3",
            source_etag='"source-etag"',
            content_type="audio/mpeg",
        )

        self.client.s3.copy_object.assert_called_once_with(
            Bucket="media",
            Key="canonical/audio/asset/object.mp3",
            CopySource={
                "Bucket": "private-media",
                "Key": "temporary/uploads/asset/session.mp3",
            },
            CopySourceIfMatch='"source-etag"',
            MetadataDirective="REPLACE",
            ContentType="audio/mpeg",
        )
        self.assertEqual(result.resource_id, "canonical/audio/asset/object.mp3")

    def test_promotion_without_source_etag_is_rejected_before_copy(self):
        with self.assertRaisesMessage(MediaProviderError, "ETag"):
            self.adapter.promote(
                source_container="private-media",
                source_key="temporary/uploads/asset/session.mp3",
                destination_key="canonical/audio/asset/object.mp3",
                source_etag="",
                content_type="audio/mpeg",
            )

        self.client.s3.copy_object.assert_not_called()

    def test_copy_succeeded_but_head_missing_is_reported_for_reconciliation(self):
        self.client.head.return_value = None

        with self.assertRaises(MediaProviderError) as raised:
            self.adapter.promote(
                source_container="private-media",
                source_key="temporary/uploads/asset/session.mp3",
                destination_key="canonical/audio/asset/object.mp3",
                source_etag='"source-etag"',
                content_type="audio/mpeg",
            )

        self.assertEqual(raised.exception.operation, "r2.copy_object")
        self.client.s3.copy_object.assert_called_once()

    def test_private_download_uses_presign_for_private_bucket(self):
        expires_at = NOW + timedelta(minutes=5)
        self.client.presign_get.return_value = TemporaryURL(
            "https://r2.example.test/?signed=download",
            expires_at,
        )

        descriptor = self.adapter.create_download_capability(
            key="premium/audio.mp3",
            expires_in=300,
        )

        self.client.presign_get.assert_called_once_with(
            "premium/audio.mp3",
            expires_in=300,
            response_content_disposition=None,
        )
        self.assertTrue(descriptor.protected)
        self.assertEqual(descriptor.expires_at, expires_at)

    def test_private_download_rejects_public_bucket(self):
        self.client.settings = R2Settings(
            account_id="account-id",
            access_key_id="access",
            secret_access_key="secret",
            bucket_name="public-media",
            public_base_url="https://media.example.test",
        )

        with self.assertRaisesMessage(
            MediaProviderError,
            "Protected R2 delivery cannot use a public bucket",
        ):
            self.adapter.create_download_capability(
                key="premium/audio.mp3",
                expires_in=300,
            )

        self.client.presign_get.assert_not_called()


class ImagesAdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = mock.Mock()
        self.signer = mock.Mock()
        self.adapter = CloudflareImagePlatform(
            self.client,
            account_hash="account-hash",
            signer=self.signer,
        )

    def test_private_upload_requires_signed_delivery(self):
        self.client.create_direct_upload.return_value = ImagesDirectUpload(
            image_id="provider-image",
            upload_url="https://upload.imagedelivery.net/secret",
        )
        expires_at = NOW + timedelta(minutes=10)

        intent = self.adapter.create_upload_intent(
            creator_id="user-1",
            metadata={"sanfootball_asset_id": "asset-1"},
            private=True,
            expires_at=expires_at,
        )

        self.client.create_direct_upload.assert_called_once_with(
            creator="user-1",
            expiry=expires_at,
            metadata={"sanfootball_asset_id": "asset-1"},
            require_signed_urls=True,
        )
        self.assertEqual(intent.resource_id, "provider-image")

    def test_private_variant_is_signed_server_side(self):
        expires_at = NOW + timedelta(minutes=5)
        self.signer.sign.return_value = "https://imagedelivery.net/signed?exp=1&sig=2"

        result = self.adapter.sign_private_variant(
            image_id="provider-image",
            variant="thumbnail",
            expires_at=expires_at,
        )

        unsigned = "https://imagedelivery.net/account-hash/provider-image/thumbnail"
        self.signer.sign.assert_called_once_with(unsigned, expires_at=expires_at)
        self.assertTrue(result.protected)
        self.assertEqual(result.expires_at, expires_at)


class StreamAdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = mock.Mock()
        self.builder = mock.Mock()
        self.builder.hls.side_effect = lambda value: f"https://stream/hls/{value}"
        self.builder.dash.side_effect = lambda value: f"https://stream/dash/{value}"
        self.builder.iframe.side_effect = lambda value: f"https://stream/iframe/{value}"
        self.builder.download.side_effect = lambda value: f"https://stream/download/{value}"
        self.verifier = mock.Mock()
        self.signer = mock.Mock()
        self.adapter = CloudflareVideoPlatform(
            self.client,
            url_builder=self.builder,
            webhook_verifier=self.verifier,
            token_signer=self.signer,
        )

    def test_small_private_video_uses_direct_creator_upload(self):
        self.client.create_direct_upload.return_value = StreamDirectUpload(
            video_id="video-id",
            upload_url="https://upload.cloudflarestream.com/secret",
        )
        expires_at = NOW + timedelta(minutes=10)

        result = self.adapter.create_upload_intent(
            creator_id="user-1",
            upload_length=10_000,
            max_duration_seconds=3600,
            metadata={"sanfootball_asset_id": "asset-1"},
            private=True,
            allowed_origins=("app.example.test",),
            expires_at=expires_at,
        )

        self.client.create_direct_upload.assert_called_once_with(
            max_duration_seconds=3600,
            allowed_origins=("app.example.test",),
            creator="user-1",
            expiry=expires_at,
            meta={"sanfootball_asset_id": "asset-1"},
            require_signed_urls=True,
        )
        self.assertFalse(result.resumable)

    def test_large_video_uses_direct_user_tus(self):
        self.client.create_tus_upload.return_value = TusUploadSession(
            video_id="video-id",
            upload_url="https://upload.cloudflarestream.com/tus/secret",
            upload_length=200_000_000,
            direct_user=True,
        )

        result = self.adapter.create_upload_intent(
            creator_id="user-1",
            upload_length=200_000_000,
            max_duration_seconds=3600,
            metadata={"name": "opaque.mp4"},
            private=True,
            allowed_origins=("app.example.test",),
            expires_at=NOW + timedelta(minutes=10),
        )

        call = self.client.create_tus_upload.call_args.kwargs
        self.assertTrue(call["direct_user"])
        self.assertIsNone(call["metadata"]["requiresignedurls"])
        self.assertEqual(call["metadata"]["maxdurationseconds"], "3600")
        self.assertEqual(call["metadata"]["expiry"], "2026-08-28T12:10:00Z")
        self.client.update.assert_called_once_with(
            "video-id",
            allowedOrigins=["app.example.test"],
        )
        self.assertEqual(result.expires_at, NOW + timedelta(minutes=10))
        self.assertTrue(result.resumable)

    def test_tus_origin_update_failure_deletes_the_unusable_resource(self):
        self.client.create_tus_upload.return_value = TusUploadSession(
            video_id="video-id",
            upload_url="https://upload.cloudflarestream.com/tus/secret",
            upload_length=200_000_000,
            direct_user=True,
        )
        self.client.update.side_effect = TransportError("network unavailable")

        with self.assertRaises(MediaProviderError) as raised:
            self.adapter.create_upload_intent(
                creator_id="user-1",
                upload_length=200_000_000,
                max_duration_seconds=3600,
                metadata={"name": "opaque.mp4"},
                private=True,
                allowed_origins=("app.example.test",),
                expires_at=NOW + timedelta(minutes=10),
            )

        self.assertEqual(raised.exception.operation, "stream.set_allowed_origins")
        self.client.delete.assert_called_once_with("video-id")

    def test_private_playback_never_builds_urls_from_bare_video_id(self):
        self.signer.sign.return_value = "signed-token"
        expires_at = NOW + timedelta(minutes=5)

        descriptor = self.adapter.get_playback_descriptor(
            video_id="bare-video-id",
            private=True,
            expires_at=expires_at,
        )

        self.signer.sign.assert_called_once_with(
            "bare-video-id",
            expires_at=expires_at,
            downloadable=False,
        )
        for call in (
            self.builder.hls.call_args,
            self.builder.dash.call_args,
            self.builder.iframe.call_args,
        ):
            self.assertEqual(call.args, ("signed-token",))
        self.assertNotIn("bare-video-id", " ".join(descriptor.urls.values()))

    def test_webhook_verifier_receives_exact_raw_body(self):
        body = b'{"uid":"video-id", "readyToStream":true}'
        self.verifier.verify.return_value = True

        result = self.adapter.verify_webhook(
            raw_body=body,
            signature_header="time=1,sig1=abc",
        )

        self.assertTrue(result)
        self.verifier.verify.assert_called_once_with(body, "time=1,sig1=abc")
