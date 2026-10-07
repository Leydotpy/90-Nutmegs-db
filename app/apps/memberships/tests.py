import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.category.models import Category
from apps.media.audio.models import Audio
from apps.media.canonical import MediaAccessClass, MediaAsset, MediaLocation, MediaVariant
from apps.media.delivery_service import MediaDeliveryService
from apps.memberships.access import AccessService
from apps.memberships.models import Entitlement, Feature, Membership, Plan, Subscription
from apps.memberships.policies import AccessAction, AccessPolicy, AccessReason
from apps.posts.podcasts.models import Episode, Podcast


class AccessPolicyMatrixTests(TestCase):
    """Behavioral matrix for the first canonical episode-access increment."""

    def setUp(self):
        cache.clear()
        AccessService._instance = None
        self.now = timezone.now().replace(microsecond=0)
        self.policy = AccessPolicy()
        self.podcast = Podcast.objects.create(
            title="Policy test podcast",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        self.free = Plan.objects.create(name="Free", tier=Plan.Level.FREE)
        self.fan = Plan.objects.create(name="Fan", tier=Plan.Level.FAN)
        self.pro = Plan.objects.create(name="Pro", tier=Plan.Level.PRO)
        self.user = self.create_user("listener")

    @staticmethod
    def create_user(username, **extra):
        return get_user_model().objects.create(
            username=username,
            clerk_user_id=f"clerk_{username}",
            **extra,
        )

    def create_episode(
        self,
        *,
        released=True,
        exclusive=False,
        required_plan=None,
        preview=False,
        early_access_hours=None,
    ):
        release_at = self.now - datetime.timedelta(hours=1)
        if not released:
            release_at = self.now + datetime.timedelta(hours=24)
        episode = Episode.objects.create(
            podcast=self.podcast,
            title=f"Episode {Episode.objects.count() + 1}",
            public_release_date=release_at,
            exclusive=exclusive,
            early_access_hours=early_access_hours,
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=(Episode.Visibility.PLAN if exclusive else Episode.Visibility.PUBLIC),
            premium_available_at=release_at,
            public_available_at=None if exclusive else release_at,
            required_plan=required_plan,
        )
        if required_plan is not None:
            category = Category.objects.create(
                name=f"Gate {Category.objects.count() + 1}",
                tier=required_plan,
            )
            episode.categories.add(category)
        if preview:
            Audio.objects.create(
                episode=episode,
                name="Preview",
                quality=Audio.Quality.PREVIEW,
                file=f"previews/{episode.pk}.mp3",
            )
        return episode

    def subscribe(
        self,
        user,
        plan,
        *,
        status=Subscription.Status.ACTIVE,
        end_date=None,
        trial_ends=None,
    ):
        membership = Membership.objects.create(user=user, plan=plan)
        return Subscription.objects.create(
            membership=membership,
            subscription_id=f"sub_{user.pk}",
            status=status,
            start_date=self.now - datetime.timedelta(seconds=1),
            end_date=end_date,
            trial_ends=trial_ends,
        )

    def entitlement(self, user, resource, *, expires_at=None, revoked=False):
        return Entitlement.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(resource),
            object_id=str(resource.pk),
            expires_at=expires_at,
            revoked=revoked,
        )

    def evaluate(self, user, episode, action=AccessAction.STREAM):
        return self.policy.evaluate(
            user=user,
            resource=episode,
            action=action,
            now=self.now,
        )

    def test_anonymous_and_free_user_can_stream_public_release(self):
        episode = self.create_episode()

        anonymous = self.evaluate(AnonymousUser(), episode)
        free_user = self.evaluate(self.user, episode)

        self.assertTrue(anonymous.allowed)
        self.assertEqual(anonymous.reason, AccessReason.PUBLIC)
        self.assertEqual(anonymous.principal_id, "")
        self.assertTrue(free_user.allowed)
        self.assertEqual(free_user.reason, AccessReason.PUBLIC)
        self.assertEqual(free_user.principal_id, str(self.user.pk))

    def test_editorial_status_gate_hides_draft_even_with_legacy_release_and_entitlement(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Canonical draft",
            status=Episode.PublicationStatus.DRAFT,
            visibility=Episode.Visibility.PUBLIC,
            public_release_date=self.now - datetime.timedelta(days=1),
            premium_available_at=self.now - datetime.timedelta(days=1),
            public_available_at=self.now - datetime.timedelta(days=1),
        )
        self.entitlement(self.user, episode)

        metadata = self.evaluate(self.user, episode, AccessAction.VIEW_METADATA)
        stream = self.evaluate(self.user, episode, AccessAction.STREAM)

        self.assertFalse(metadata.allowed)
        self.assertEqual(metadata.reason, AccessReason.NOT_YET_RELEASED)
        self.assertFalse(stream.allowed)
        self.assertEqual(stream.reason, AccessReason.NOT_YET_RELEASED)

    def test_published_episode_under_draft_podcast_fails_closed(self):
        episode = self.create_episode()
        self.podcast.status = Podcast.PublicationStatus.DRAFT
        self.podcast.published_at = None
        self.podcast.save(update_fields=("status", "published_at", "updated"))

        decision = self.evaluate(AnonymousUser(), episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.NOT_YET_RELEASED)

    def test_unreconciled_child_owned_episode_fails_closed(self):
        parent = Podcast.objects.create(
            title="Canonical parent",
            structure=Podcast.Structure.PARENT,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        child = Podcast.objects.create(
            title="Unreconciled child",
            structure=Podcast.Structure.CHILD,
            parent=parent,
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=self.now - datetime.timedelta(hours=1),
        )
        episode = self.create_episode()
        Episode.objects.filter(pk=episode.pk).update(podcast=child)
        episode.refresh_from_db()

        decision = self.evaluate(AnonymousUser(), episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.NOT_YET_RELEASED)

    def test_categories_are_tags_not_live_commercial_policy(self):
        episode = self.create_episode()
        category = Category.objects.create(name="Legacy pro tag", tier=self.pro)
        episode.categories.add(category)

        decision = self.evaluate(AnonymousUser(), episode)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.PUBLIC)
        self.assertIsNone(decision.required_plan)

    def test_explicit_premium_and_public_windows_are_independent(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Windowed release",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
            required_plan=self.fan,
            premium_available_at=self.now - datetime.timedelta(minutes=1),
            public_available_at=self.now + datetime.timedelta(hours=1),
        )
        fan_user = self.create_user("windowed_fan")
        subscription = self.subscribe(fan_user, self.fan)

        anonymous_before = self.evaluate(AnonymousUser(), episode)
        fan_before = self.evaluate(fan_user, episode)
        anonymous_after = self.policy.evaluate(
            user=AnonymousUser(),
            resource=episode,
            action=AccessAction.STREAM,
            now=self.now + datetime.timedelta(hours=2),
        )

        self.assertFalse(anonymous_before.allowed)
        self.assertTrue(fan_before.allowed)
        self.assertEqual(fan_before.reason, AccessReason.ACTIVE_PLAN)
        self.assertEqual(fan_before.effective_subscription, subscription)
        self.assertTrue(anonymous_after.allowed)
        self.assertEqual(anonymous_after.reason, AccessReason.PUBLIC)

    def test_plan_visibility_without_explicit_required_plan_fails_closed(self):
        episode = Episode.objects.create(
            podcast=self.podcast,
            title="Unconfigured plan gate",
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
            premium_available_at=self.now - datetime.timedelta(minutes=1),
        )
        fan_user = self.create_user("unconfigured_plan_fan")
        self.subscribe(fan_user, self.fan)

        decision = self.evaluate(fan_user, episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.REQUIRES_PLAN)

    def test_anonymous_premium_denial_reports_login_and_preview(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan, preview=True)

        decision = self.evaluate(AnonymousUser(), episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.REQUIRES_LOGIN)
        self.assertEqual(decision.required_plan, self.fan)
        self.assertTrue(decision.preview_allowed)

    def test_free_user_premium_denial_reports_required_plan(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)

        decision = self.evaluate(self.user, episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.REQUIRES_PLAN)
        self.assertEqual(decision.required_plan, self.fan)

    def test_plan_ranking_allows_higher_but_not_lower_tier(self):
        fan_episode = self.create_episode(exclusive=True, required_plan=self.fan)
        pro_episode = self.create_episode(exclusive=True, required_plan=self.pro)
        fan_user = self.create_user("fan")
        pro_user = self.create_user("pro")
        fan_subscription = self.subscribe(fan_user, self.fan)
        pro_subscription = self.subscribe(pro_user, self.pro)

        fan_to_fan = self.evaluate(fan_user, fan_episode)
        fan_to_pro = self.evaluate(fan_user, pro_episode)
        pro_to_fan = self.evaluate(pro_user, fan_episode)

        self.assertTrue(fan_to_fan.allowed)
        self.assertEqual(fan_to_fan.effective_subscription, fan_subscription)
        self.assertFalse(fan_to_pro.allowed)
        self.assertTrue(pro_to_fan.allowed)
        self.assertEqual(pro_to_fan.effective_subscription, pro_subscription)

    def test_current_trial_grants_access_but_past_due_does_not(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)
        trial_user = self.create_user("trial")
        past_due_user = self.create_user("past_due")
        self.subscribe(
            trial_user,
            self.fan,
            status=Subscription.Status.TRIAL,
            trial_ends=self.now + datetime.timedelta(days=3),
        )
        self.subscribe(past_due_user, self.fan, status=Subscription.Status.PAST_DUE)

        trial = self.evaluate(trial_user, episode)
        past_due = self.evaluate(past_due_user, episode)

        self.assertTrue(trial.allowed)
        self.assertEqual(trial.reason, AccessReason.ACTIVE_PLAN)
        self.assertFalse(past_due.allowed)
        self.assertEqual(past_due.reason, AccessReason.EXPIRED)

    def test_cancel_at_period_end_grants_until_expiry(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)
        current_user = self.create_user("canceling")
        expired_user = self.create_user("canceled")
        self.subscribe(
            current_user,
            self.fan,
            status=Subscription.Status.CANCELED,
            end_date=self.now + datetime.timedelta(days=2),
        )
        self.subscribe(
            expired_user,
            self.fan,
            status=Subscription.Status.CANCELED,
            end_date=self.now - datetime.timedelta(seconds=1),
        )

        self.assertTrue(self.evaluate(current_user, episode).allowed)
        expired = self.evaluate(expired_user, episode)
        self.assertFalse(expired.allowed)
        self.assertEqual(expired.reason, AccessReason.EXPIRED)

    def test_explicitly_expired_subscription_does_not_grant(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)
        expired_user = self.create_user("explicitly_expired")
        self.subscribe(
            expired_user,
            self.fan,
            status=Subscription.Status.EXPIRED,
        )

        decision = self.evaluate(expired_user, episode)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.EXPIRED)

    def test_direct_entitlement_uses_actual_resource_and_reports_it(self):
        episode = self.create_episode(exclusive=True, required_plan=self.pro)
        entitlement = self.entitlement(self.user, episode)

        decision = self.evaluate(self.user, episode)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.ENTITLEMENT)
        self.assertEqual(decision.effective_entitlement, entitlement)

    def test_expired_and_revoked_entitlements_fail_closed(self):
        expired_episode = self.create_episode(exclusive=True, required_plan=self.pro)
        revoked_episode = self.create_episode(exclusive=True, required_plan=self.pro)
        self.entitlement(
            self.user,
            expired_episode,
            expires_at=self.now - datetime.timedelta(seconds=1),
        )
        self.entitlement(self.user, revoked_episode, revoked=True)

        expired = self.evaluate(self.user, expired_episode)
        revoked = self.evaluate(self.user, revoked_episode)

        self.assertFalse(expired.allowed)
        self.assertEqual(expired.reason, AccessReason.EXPIRED)
        self.assertFalse(revoked.allowed)
        self.assertEqual(revoked.reason, AccessReason.REVOKED)

    def test_staff_bypass_is_explicit(self):
        episode = self.create_episode(released=False, exclusive=True, required_plan=self.pro)
        staff = self.create_user("staff", is_staff=True)

        decision = self.evaluate(staff, episode)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.STAFF_BYPASS)

    def test_early_access_is_limited_to_feature_window(self):
        feature = Feature.objects.create(
            kind=Feature.Kind.EARLY_ACCESS,
            early_access_hours=12,
        )
        self.fan.features.add(feature)
        fan_user = self.create_user("early_fan")
        self.subscribe(fan_user, self.fan)
        episode = self.create_episode(released=False, required_plan=self.fan)

        before_window = self.evaluate(fan_user, episode)
        episode.public_release_date = self.now + datetime.timedelta(hours=6)
        episode.premium_available_at = episode.public_release_date
        episode.public_available_at = episode.public_release_date
        episode.save(
            update_fields=[
                "public_release_date",
                "premium_available_at",
                "public_available_at",
            ]
        )
        inside_window = self.evaluate(fan_user, episode)

        self.assertFalse(before_window.allowed)
        self.assertEqual(before_window.reason, AccessReason.NOT_YET_RELEASED)
        self.assertTrue(inside_window.allowed)
        self.assertEqual(inside_window.reason, AccessReason.EARLY_ACCESS)

    def test_episode_early_access_hours_override_the_plan_window(self):
        feature = Feature.objects.create(
            kind=Feature.Kind.EARLY_ACCESS,
            early_access_hours=12,
        )
        self.fan.features.add(feature)
        fan_user = self.create_user("override_early_fan")
        self.subscribe(fan_user, self.fan)
        episode = self.create_episode(
            released=False,
            required_plan=self.fan,
            early_access_hours=1,
        )

        two_hours_before = self.policy.evaluate(
            user=fan_user,
            resource=episode,
            action=AccessAction.STREAM,
            now=episode.public_release_date - datetime.timedelta(hours=2),
        )
        thirty_minutes_before = self.policy.evaluate(
            user=fan_user,
            resource=episode,
            action=AccessAction.STREAM,
            now=episode.public_release_date - datetime.timedelta(minutes=30),
        )

        self.assertFalse(two_hours_before.allowed)
        self.assertEqual(two_hours_before.reason, AccessReason.NOT_YET_RELEASED)
        self.assertTrue(thirty_minutes_before.allowed)
        self.assertEqual(thirty_minutes_before.reason, AccessReason.EARLY_ACCESS)

    def test_preview_unavailable_is_reported(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)

        decision = self.evaluate(AnonymousUser(), episode)

        self.assertFalse(decision.preview_allowed)

    def test_download_needs_an_active_plan_download_capability(self):
        downloadable = Feature.objects.create(kind=Feature.Kind.DOWNLOADABLE)
        self.fan.features.add(downloadable)
        fan_user = self.create_user("downloader")
        no_download_user = self.create_user("stream_only")
        subscription = self.subscribe(fan_user, self.fan)
        self.subscribe(no_download_user, self.pro)
        episode = self.create_episode(exclusive=True, required_plan=self.fan)

        allowed = self.evaluate(fan_user, episode, AccessAction.DOWNLOAD)
        denied = self.evaluate(no_download_user, episode, AccessAction.DOWNLOAD)

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.effective_subscription, subscription)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.reason, AccessReason.REQUIRES_PLAN)

    def test_stream_entitlement_does_not_implicitly_grant_download(self):
        episode = self.create_episode(exclusive=True, required_plan=self.fan)
        self.entitlement(self.user, episode)

        stream = self.evaluate(self.user, episode, AccessAction.STREAM)
        download = self.evaluate(self.user, episode, AccessAction.DOWNLOAD)

        self.assertTrue(stream.allowed)
        self.assertFalse(download.allowed)

    def test_transcript_uses_same_resource_gate_as_stream(self):
        public_episode = self.create_episode()
        premium_episode = self.create_episode(exclusive=True, required_plan=self.fan)

        public = self.evaluate(AnonymousUser(), public_episode, AccessAction.VIEW_TRANSCRIPT)
        premium = self.evaluate(self.user, premium_episode, AccessAction.VIEW_TRANSCRIPT)

        self.assertTrue(public.allowed)
        self.assertFalse(premium.allowed)

    def test_premium_metadata_remains_public_but_commenting_requires_login(self):
        episode = self.create_episode(exclusive=True, required_plan=self.pro)

        metadata = self.evaluate(AnonymousUser(), episode, AccessAction.VIEW_METADATA)
        comment = self.evaluate(AnonymousUser(), episode, AccessAction.COMMENT)

        self.assertTrue(metadata.allowed)
        self.assertFalse(comment.allowed)
        self.assertEqual(comment.reason, AccessReason.REQUIRES_LOGIN)

    def test_real_media_decision_binds_variant_and_drives_delivery(self):
        episode = self.create_episode()
        asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            access_class=MediaAccessClass.PUBLIC,
            status=MediaAsset.Status.READY,
            mime_type="audio/mpeg",
            byte_size=1024,
        )
        variant = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_STANDARD,
            status=MediaVariant.Status.READY,
        )
        location = MediaLocation.objects.create(
            asset=asset,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container="public-media",
            locator="canonical/audio/public.mp3",
            status=MediaLocation.Status.AVAILABLE,
            is_primary=True,
        )
        anonymous = AnonymousUser()
        decision = self.policy.evaluate_media(
            user=anonymous,
            resource=episode,
            variant=variant,
            action=AccessAction.STREAM,
            now=self.now,
        )
        public_objects = mock.Mock()
        public_objects.build_public_url.return_value = mock.sentinel.descriptor
        service = MediaDeliveryService(
            private_object_storage=mock.Mock(),
            public_object_storage=public_objects,
            image_platform=mock.Mock(),
            video_platform=mock.Mock(),
            private_container="private-media",
            public_container="public-media",
            private_ttl_seconds=300,
        )

        result = service.deliver_object(
            decision=decision,
            actor=anonymous,
            variant=variant,
            location=location,
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.media_variant_id, str(variant.pk))
        self.assertEqual(decision.media_access_class, MediaAccessClass.PUBLIC)
        self.assertIs(result, mock.sentinel.descriptor)

    def test_public_episode_decision_does_not_grant_premium_variant(self):
        episode = self.create_episode()
        asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            access_class=MediaAccessClass.PREMIUM,
            status=MediaAsset.Status.READY,
            mime_type="audio/mpeg",
            byte_size=1024,
        )
        variant = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_STANDARD,
            status=MediaVariant.Status.READY,
        )

        decision = self.policy.evaluate_media(
            user=AnonymousUser(),
            resource=episode,
            variant=variant,
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.media_variant_id, str(variant.pk))
        self.assertEqual(decision.media_access_class, MediaAccessClass.PREMIUM)

    def test_paid_subscriber_can_deliver_ad_free_variant_for_public_episode(self):
        episode = self.create_episode()
        expires_at = self.now + datetime.timedelta(seconds=120)
        subscription = self.subscribe(
            self.user,
            self.fan,
            end_date=expires_at,
        )
        asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            access_class=MediaAccessClass.AD_FREE,
            status=MediaAsset.Status.READY,
            mime_type="audio/mpeg",
            byte_size=1024,
        )
        variant = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_STANDARD,
            status=MediaVariant.Status.READY,
        )
        location = MediaLocation.objects.create(
            asset=asset,
            provider=MediaLocation.Provider.CLOUDFLARE,
            product=MediaLocation.Product.R2,
            container="private-media",
            locator="canonical/audio/ad-free.mp3",
            status=MediaLocation.Status.AVAILABLE,
            is_primary=True,
        )
        decision = self.policy.evaluate_media(
            user=self.user,
            resource=episode,
            variant=variant,
            action=AccessAction.STREAM,
            now=self.now,
        )
        private_objects = mock.Mock()
        private_objects.create_download_capability.return_value = mock.sentinel.descriptor
        service = MediaDeliveryService(
            private_object_storage=private_objects,
            public_object_storage=mock.Mock(),
            image_platform=mock.Mock(),
            video_platform=mock.Mock(),
            private_container="private-media",
            public_container="public-media",
            private_ttl_seconds=300,
        )

        result = service.deliver_object(
            decision=decision,
            actor=self.user,
            variant=variant,
            location=location,
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.ACTIVE_PLAN)
        self.assertEqual(decision.effective_subscription, subscription)
        self.assertEqual(decision.principal_id, str(self.user.pk))
        self.assertEqual(decision.media_variant_id, str(variant.pk))
        self.assertEqual(decision.media_access_class, MediaAccessClass.AD_FREE)
        self.assertEqual(decision.expires_at, expires_at)
        self.assertIs(result, mock.sentinel.descriptor)
        private_objects.create_download_capability.assert_called_once_with(
            key=location.locator,
            expires_in=120,
            response_content_disposition=None,
        )

    def test_free_subscription_does_not_grant_ad_free_public_episode_variant(self):
        episode = self.create_episode()
        self.subscribe(self.user, self.free)
        asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            access_class=MediaAccessClass.AD_FREE,
            status=MediaAsset.Status.READY,
            mime_type="audio/mpeg",
            byte_size=1024,
        )
        variant = MediaVariant.objects.create(
            episode=episode,
            asset=asset,
            kind=MediaVariant.Kind.AUDIO_STANDARD,
            status=MediaVariant.Status.READY,
        )

        decision = self.policy.evaluate_media(
            user=self.user,
            resource=episode,
            variant=variant,
            action=AccessAction.STREAM,
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.REQUIRES_PLAN)
        self.assertEqual(decision.principal_id, str(self.user.pk))
        self.assertEqual(decision.media_variant_id, str(variant.pk))
        self.assertEqual(decision.media_access_class, MediaAccessClass.AD_FREE)

    def test_compatibility_cache_key_separates_action_and_policy_version(self):
        episode = self.create_episode()

        stream_key = AccessService._cache_key(self.user, episode, AccessAction.STREAM)
        download_key = AccessService._cache_key(self.user, episode, AccessAction.DOWNLOAD)

        self.assertNotEqual(stream_key, download_key)
        self.assertIn(AccessPolicy.VERSION, stream_key)

    def test_cache_failure_cannot_turn_policy_denial_into_access(self):
        class BrokenCache:
            def get(self, _key):
                raise ConnectionError("cache unavailable")

            def set(self, *_args, **_kwargs):
                raise ConnectionError("cache unavailable")

        episode = self.create_episode(exclusive=True, required_plan=self.pro)
        service = AccessService(cache_backend=BrokenCache(), policy=self.policy)

        self.assertFalse(service.has_access(self.user, episode, AccessAction.STREAM))
