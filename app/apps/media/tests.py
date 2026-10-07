"""Canonical media asset and location invariants."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.media.models import MediaAsset, MediaLocation, MediaVariant
from apps.posts.podcasts.models import Episode, Podcast


class MediaAssetConstraintTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username="media-owner",
            clerk_user_id="clerk_media_owner",
        )

    def asset(self, **overrides):
        values = {
            "created_by": self.user,
            "media_type": MediaAsset.MediaType.AUDIO,
        }
        values.update(overrides)
        return MediaAsset.objects.create(**values)

    def test_one_provider_locator_cannot_identify_two_assets(self):
        first = self.asset()
        second = self.asset()
        MediaLocation.objects.create(
            asset=first,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            locator="published/audio/opaque.mp3",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaLocation.objects.create(
                asset=second,
                provider=MediaLocation.Provider.CLOUDFLARE,
                product=MediaLocation.Product.R2,
                locator="published/audio/opaque.mp3",
            )

    def test_same_locator_is_allowed_in_distinct_provider_containers(self):
        first = self.asset()
        second = self.asset()

        MediaLocation.objects.create(
            asset=first,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container="sanfootball-private",
            locator="temporary/uploads/opaque.mp3",
        )
        other = MediaLocation.objects.create(
            asset=second,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container="sanfootball-public",
            locator="temporary/uploads/opaque.mp3",
        )

        self.assertEqual(other.asset, second)

    def test_asset_has_at_most_one_primary_location(self):
        asset = self.asset()
        MediaLocation.objects.create(
            asset=asset,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            locator="source/audio.mp3",
            is_primary=True,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaLocation.objects.create(
                asset=asset,
                provider=MediaLocation.Provider.LEGACY_AWS,
                product=MediaLocation.Product.S3,
                locator="legacy/audio.mp3",
                is_primary=True,
            )

    def test_asset_cannot_be_its_own_source(self):
        asset = self.asset()

        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaAsset.objects.filter(pk=asset.pk).update(source_asset=asset)

    def test_creator_idempotency_key_is_unique_but_blank_keys_are_not(self):
        self.asset(upload_idempotency_key="request-1")
        self.asset()
        self.asset()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.asset(upload_idempotency_key="request-1")

    def test_episode_cannot_repeat_same_asset_kind(self):
        podcast = Podcast.objects.create(title="Variant constraints")
        episode = Episode.objects.create(podcast=podcast, title="Episode")
        asset = self.asset()
        MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_MASTER,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaVariant.objects.create(
                episode=episode,
                asset=asset,
                kind=MediaVariant.Kind.AUDIO_MASTER,
            )

    def test_variant_can_override_asset_access_class(self):
        podcast = Podcast.objects.create(title="Variant access")
        episode = Episode.objects.create(podcast=podcast, title="Episode")
        asset = self.asset(access_class="public")

        inherited = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_MASTER,
        )
        protected = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.PREVIEW,
            access_class="premium",
        )

        self.assertEqual(inherited.effective_access_class, "public")
        self.assertEqual(protected.effective_access_class, "premium")
