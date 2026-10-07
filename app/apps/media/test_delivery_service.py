from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest import mock
from uuid import uuid4

from django.test import SimpleTestCase

from apps.media.canonical import MediaAccessClass, MediaAsset, MediaLocation, MediaVariant
from apps.media.delivery_service import MediaDeliveryDenied, MediaDeliveryService
from apps.media.providers.contracts import DeliveryDescriptor
from apps.memberships.policies import AccessAction


class MediaDeliveryServiceTests(SimpleTestCase):
    def setUp(self):
        self.private_objects = mock.Mock()
        self.public_objects = mock.Mock()
        self.images = mock.Mock()
        self.video = mock.Mock()
        self.service = MediaDeliveryService(
            private_object_storage=self.private_objects,
            public_object_storage=self.public_objects,
            image_platform=self.images,
            video_platform=self.video,
            private_container="private-media",
            public_container="public-media",
            private_ttl_seconds=300,
        )
        self.now = datetime(2026, 8, 28, 12, tzinfo=UTC)
        self.episode_id = uuid4()
        self.asset_id = uuid4()
        self.variant_id = uuid4()
        self.actor = SimpleNamespace(pk=uuid4(), is_authenticated=True)

    def variant(
        self,
        *,
        access_class=MediaAccessClass.PREMIUM,
        asset_status=MediaAsset.Status.READY,
    ):
        return SimpleNamespace(
            pk=self.variant_id,
            episode_id=self.episode_id,
            asset_id=self.asset_id,
            asset=SimpleNamespace(status=asset_status),
            status=MediaVariant.Status.READY,
            effective_access_class=access_class,
        )

    def location(
        self,
        *,
        product=MediaLocation.Product.R2,
        container="private-media",
        requires_signed_delivery=True,
        provider=MediaLocation.Provider.CLOUDFLARE,
    ):
        return SimpleNamespace(
            asset_id=self.asset_id,
            provider=provider,
            product=product,
            locator="provider-resource-id",
            container=container,
            metadata={"requires_signed_delivery": requires_signed_delivery},
            status=MediaLocation.Status.AVAILABLE,
        )

    def decision(
        self,
        *,
        action=AccessAction.STREAM,
        allowed=True,
        access_class=MediaAccessClass.PREMIUM,
        expires_at=None,
    ):
        return SimpleNamespace(
            allowed=allowed,
            action=action,
            resource_label="podcasts.episode",
            resource_id=str(self.episode_id),
            principal_id=str(self.actor.pk),
            media_variant_id=str(self.variant_id),
            media_access_class=access_class,
            expires_at=expires_at,
        )

    def assert_no_provider_calls(self):
        self.assertEqual(self.private_objects.mock_calls, [])
        self.assertEqual(self.public_objects.mock_calls, [])
        self.assertEqual(self.images.mock_calls, [])
        self.assertEqual(self.video.mock_calls, [])

    def test_denial_mints_no_provider_capability(self):
        with self.assertRaises(MediaDeliveryDenied):
            self.service.deliver_object(
                decision=self.decision(allowed=False),
                actor=self.actor,
                variant=self.variant(),
                location=self.location(),
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_protected_object_uses_bound_location_and_internal_ttl(self):
        descriptor = DeliveryDescriptor(
            provider="cloudflare",
            product="r2",
            resource_id="provider-resource-id",
            urls={"download": "https://signed.example.test"},
        )
        self.private_objects.create_download_capability.return_value = descriptor

        result = self.service.deliver_object(
            decision=self.decision(),
            actor=self.actor,
            variant=self.variant(),
            location=self.location(),
            action=AccessAction.STREAM,
        )

        self.assertIs(result, descriptor)
        self.private_objects.create_download_capability.assert_called_once_with(
            key="provider-resource-id",
            expires_in=300,
            response_content_disposition=None,
        )
        self.public_objects.build_public_url.assert_not_called()

    def test_public_object_uses_only_public_bucket(self):
        self.public_objects.build_public_url.return_value = mock.sentinel.descriptor

        result = self.service.deliver_object(
            decision=self.decision(access_class=MediaAccessClass.PUBLIC),
            actor=self.actor,
            variant=self.variant(access_class=MediaAccessClass.PUBLIC),
            location=self.location(container="public-media"),
            action=AccessAction.STREAM,
        )

        self.assertIs(result, mock.sentinel.descriptor)
        self.public_objects.build_public_url.assert_called_once_with(key="provider-resource-id")
        self.private_objects.create_download_capability.assert_not_called()

    def test_public_object_in_private_container_is_denied(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "visibility"):
            self.service.deliver_object(
                decision=self.decision(access_class=MediaAccessClass.PUBLIC),
                actor=self.actor,
                variant=self.variant(access_class=MediaAccessClass.PUBLIC),
                location=self.location(container="private-media"),
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_protected_object_in_public_container_is_denied(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "visibility"):
            self.service.deliver_object(
                decision=self.decision(),
                actor=self.actor,
                variant=self.variant(access_class=MediaAccessClass.PREMIUM),
                location=self.location(container="public-media"),
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_private_image_is_signed_with_internal_expiry(self):
        self.service.deliver_image(
            decision=self.decision(),
            actor=self.actor,
            variant=self.variant(),
            location=self.location(product=MediaLocation.Product.IMAGES),
            image_variant="cover",
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.images.sign_private_variant.assert_called_once_with(
            image_id="provider-resource-id",
            variant="cover",
            expires_at=self.now + timedelta(seconds=300),
        )
        self.images.build_public_variant.assert_not_called()

    def test_managed_visibility_mismatch_is_denied(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "visibility"):
            self.service.deliver_image(
                decision=self.decision(),
                actor=self.actor,
                variant=self.variant(access_class=MediaAccessClass.PREMIUM),
                location=self.location(
                    product=MediaLocation.Product.IMAGES,
                    requires_signed_delivery=False,
                ),
                image_variant="cover",
                action=AccessAction.STREAM,
                now=self.now,
            )

        self.assert_no_provider_calls()

    def test_public_managed_image_requires_verified_public_visibility(self):
        self.images.build_public_variant.return_value = mock.sentinel.descriptor

        result = self.service.deliver_image(
            decision=self.decision(access_class=MediaAccessClass.PUBLIC),
            actor=self.actor,
            variant=self.variant(access_class=MediaAccessClass.PUBLIC),
            location=self.location(
                product=MediaLocation.Product.IMAGES,
                requires_signed_delivery=False,
            ),
            image_variant="cover",
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.assertIs(result, mock.sentinel.descriptor)
        self.images.build_public_variant.assert_called_once_with(
            image_id="provider-resource-id",
            variant="cover",
        )

    def test_private_video_requests_tokenized_playback(self):
        self.service.deliver_video(
            decision=self.decision(access_class=MediaAccessClass.MEMBERS_ONLY),
            actor=self.actor,
            variant=self.variant(access_class=MediaAccessClass.MEMBERS_ONLY),
            location=self.location(product=MediaLocation.Product.STREAM),
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.video.get_playback_descriptor.assert_called_once_with(
            video_id="provider-resource-id",
            private=True,
            expires_at=self.now + timedelta(seconds=300),
            downloadable=False,
        )

    def test_decision_for_another_episode_is_rejected_before_provider_call(self):
        decision = self.decision()
        decision.resource_id = str(uuid4())

        with self.assertRaisesMessage(MediaDeliveryDenied, "episode"):
            self.service.deliver_object(
                decision=decision,
                actor=self.actor,
                variant=self.variant(),
                location=self.location(),
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_location_for_another_asset_is_rejected_before_provider_call(self):
        location = self.location()
        location.asset_id = uuid4()

        with self.assertRaisesMessage(MediaDeliveryDenied, "location"):
            self.service.deliver_object(
                decision=self.decision(),
                actor=self.actor,
                variant=self.variant(),
                location=location,
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_non_ready_asset_lifecycle_is_denied_before_provider_call(self):
        for status in (
            MediaAsset.Status.UPLOADED,
            MediaAsset.Status.FAILED,
            MediaAsset.Status.DELETED,
        ):
            with (
                self.subTest(status=status),
                self.assertRaisesMessage(MediaDeliveryDenied, "asset is not ready"),
            ):
                self.service.deliver_object(
                    decision=self.decision(),
                    actor=self.actor,
                    variant=self.variant(asset_status=status),
                    location=self.location(),
                    action=AccessAction.STREAM,
                )

        self.assert_no_provider_calls()

    def test_non_cloudflare_locations_are_denied_for_every_cloudflare_product(self):
        for product in (
            MediaLocation.Product.R2,
            MediaLocation.Product.IMAGES,
            MediaLocation.Product.STREAM,
        ):
            location = self.location(
                product=product,
                provider=MediaLocation.Provider.LEGACY_AWS,
            )
            with (
                self.subTest(product=product),
                self.assertRaisesMessage(
                    MediaDeliveryDenied,
                    "location",
                ),
            ):
                if product == MediaLocation.Product.R2:
                    self.service.deliver_object(
                        decision=self.decision(),
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        action=AccessAction.STREAM,
                    )
                elif product == MediaLocation.Product.IMAGES:
                    self.service.deliver_image(
                        decision=self.decision(),
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        image_variant="cover",
                        action=AccessAction.STREAM,
                    )
                else:
                    self.service.deliver_video(
                        decision=self.decision(),
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        action=AccessAction.STREAM,
                    )

        self.assert_no_provider_calls()

    def test_decision_for_another_principal_is_denied_before_provider_call(self):
        decision = self.decision()
        decision.principal_id = str(uuid4())

        with self.assertRaisesMessage(MediaDeliveryDenied, "principal"):
            self.service.deliver_object(
                decision=decision,
                actor=self.actor,
                variant=self.variant(),
                location=self.location(),
                action=AccessAction.STREAM,
            )

        self.assert_no_provider_calls()

    def test_public_decision_cannot_mint_a_premium_variant_capability(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "media variant"):
            self.service.deliver_object(
                decision=self.decision(access_class=MediaAccessClass.PUBLIC),
                actor=self.actor,
                variant=self.variant(access_class=MediaAccessClass.PREMIUM),
                location=self.location(),
                action=AccessAction.STREAM,
                now=self.now,
            )

        self.assert_no_provider_calls()

    def test_expired_decision_is_denied_before_provider_call(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "expired"):
            self.service.deliver_object(
                decision=self.decision(expires_at=self.now),
                actor=self.actor,
                variant=self.variant(),
                location=self.location(),
                action=AccessAction.STREAM,
                now=self.now,
            )

        self.assert_no_provider_calls()

    def test_near_expiry_clamps_r2_image_and_stream_capabilities(self):
        expires_at = self.now + timedelta(seconds=10)
        decision = self.decision(expires_at=expires_at)

        self.service.deliver_object(
            decision=decision,
            actor=self.actor,
            variant=self.variant(),
            location=self.location(),
            action=AccessAction.STREAM,
            now=self.now,
        )
        self.private_objects.create_download_capability.assert_called_once_with(
            key="provider-resource-id",
            expires_in=10,
            response_content_disposition=None,
        )

        self.service.deliver_image(
            decision=decision,
            actor=self.actor,
            variant=self.variant(),
            location=self.location(product=MediaLocation.Product.IMAGES),
            image_variant="cover",
            action=AccessAction.STREAM,
            now=self.now,
        )
        self.images.sign_private_variant.assert_called_once_with(
            image_id="provider-resource-id",
            variant="cover",
            expires_at=expires_at,
        )

        self.service.deliver_video(
            decision=decision,
            actor=self.actor,
            variant=self.variant(),
            location=self.location(product=MediaLocation.Product.STREAM),
            action=AccessAction.STREAM,
            now=self.now,
        )
        self.video.get_playback_descriptor.assert_called_once_with(
            video_id="provider-resource-id",
            private=True,
            expires_at=expires_at,
            downloadable=False,
        )

    def test_non_media_actions_cannot_mint_any_provider_capability(self):
        for product in (
            MediaLocation.Product.R2,
            MediaLocation.Product.IMAGES,
            MediaLocation.Product.STREAM,
        ):
            decision = self.decision(action=AccessAction.VIEW_METADATA)
            location = self.location(product=product)
            with (
                self.subTest(product=product),
                self.assertRaisesMessage(
                    MediaDeliveryDenied,
                    "cannot mint",
                ),
            ):
                if product == MediaLocation.Product.R2:
                    self.service.deliver_object(
                        decision=decision,
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        action=AccessAction.VIEW_METADATA,
                        now=self.now,
                    )
                elif product == MediaLocation.Product.IMAGES:
                    self.service.deliver_image(
                        decision=decision,
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        image_variant="cover",
                        action=AccessAction.VIEW_METADATA,
                        now=self.now,
                    )
                else:
                    self.service.deliver_video(
                        decision=decision,
                        actor=self.actor,
                        variant=self.variant(),
                        location=location,
                        action=AccessAction.VIEW_METADATA,
                        now=self.now,
                    )

        self.assert_no_provider_calls()

    def test_downloadable_video_requires_download_decision(self):
        with self.assertRaisesMessage(MediaDeliveryDenied, "download"):
            self.service.deliver_video(
                decision=self.decision(action=AccessAction.STREAM),
                actor=self.actor,
                variant=self.variant(),
                location=self.location(product=MediaLocation.Product.STREAM),
                action=AccessAction.STREAM,
                downloadable=True,
                now=self.now,
            )

        self.assert_no_provider_calls()

    def test_downloadable_video_accepts_exact_download_decision(self):
        self.service.deliver_video(
            decision=self.decision(action=AccessAction.DOWNLOAD),
            actor=self.actor,
            variant=self.variant(),
            location=self.location(product=MediaLocation.Product.STREAM),
            action=AccessAction.DOWNLOAD,
            downloadable=True,
            now=self.now,
        )

        self.video.get_playback_descriptor.assert_called_once_with(
            video_id="provider-resource-id",
            private=True,
            expires_at=self.now + timedelta(seconds=300),
            downloadable=True,
        )
