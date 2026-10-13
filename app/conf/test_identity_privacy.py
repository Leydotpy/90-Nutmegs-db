"""Privacy boundaries for identity and generic resource representations."""

import json
from unittest import mock

from api.rest.dashboard.apps.memberships.serializers import EntitlementDisplaySerializer
from api.rest.dashboard.apps.podcasts.serializers import (
    EpisodeModelSerializer,
    PodcastModelSerializer,
    PodcastSerializer,
)
from api.rest.web.serializers.auth import UserDisplaySerializer
from api.rest.web.serializers.membership import (
    MembershipSerializer,
    PlanModelSerializer,
    SubscriptionSerializer,
)
from apps.media.offline.models import License
from apps.memberships.models import Entitlement, Membership, Plan, Subscription
from apps.posts.podcasts.models import Episode, Podcast
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class IdentityPrivacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="private-follower",
            email="private-follower@example.test",
            clerk_user_id="clerk-private-follower",
            password="private-password",
            first_name="Private",
            last_name="Follower",
        )
        cls.podcast = Podcast.objects.create(
            title="Privacy fixture",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        cls.podcast.subscribers.add(cls.user)
        cls.episode = Episode.objects.create(podcast=cls.podcast, title="Private audience")

    def assert_no_follower_identity(self, data):
        def values(value):
            if isinstance(value, dict):
                for nested in value.values():
                    yield from values(nested)
            elif isinstance(value, (list, tuple)):
                for nested in value:
                    yield from values(nested)
            else:
                yield value

        self.assertNotIn(self.user.pk, list(values(data)))
        self.assertNotIn(str(self.user.pk), list(values(data)))
        payload = json.dumps(data, default=str)
        for value in (
            self.user.username,
            self.user.email,
            self.user.clerk_user_id,
            '"subscribers"',
        ):
            self.assertNotIn(value, payload)

    def test_public_user_representation_has_only_display_identity(self):
        with self.assertNumQueries(0):
            data = UserDisplaySerializer(self.user).data
        self.assertEqual(
            set(data),
            {"id", "username", "first_name", "last_name", "image", "fullname", "name"},
        )
        self.assertNotIn(self.user.email, json.dumps(data))
        self.assertNotIn(self.user.clerk_user_id, json.dumps(data))
        self.assertNotIn(self.user.password, json.dumps(data))

    def test_public_podcast_exposes_count_and_current_user_state_only(self):
        client = APIClient()
        url = f"/api/rest/web/apps/podcast/{self.podcast.slug}/"
        for user, expected_following in ((None, False), (self.user, True)):
            with self.subTest(authenticated=user is not None):
                client.force_authenticate(user=user)
                response = client.get(url)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["subscriber_count"], 1)
                self.assertEqual(response.data["user_has_subscribed"], expected_following)
                self.assert_no_follower_identity(response.data)

    def test_dashboard_podcast_and_nested_episode_hide_follower_identities(self):
        for serializer in (
            PodcastSerializer(self.podcast),
            PodcastModelSerializer(self.podcast),
            EpisodeModelSerializer(self.episode),
        ):
            with self.subTest(serializer=type(serializer).__name__):
                data = serializer.data
                self.assert_no_follower_identity(data)
                podcast_data = data.get("podcast", data)
                self.assertEqual(podcast_data["subscriber_count"], 1)

    def test_dashboard_podcast_edit_cannot_overwrite_follows(self):
        serializer = PodcastSerializer(
            self.podcast,
            data={"title": "Edited title", "subscribers": [], "subscriber_count": 0},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.assertEqual(self.podcast.subscribers.count(), 1)
        self.assertEqual(self.podcast.title, "Edited title")
        self.assert_no_follower_identity(serializer.data)

    def test_entitlement_known_resources_do_not_restore_follower_lists(self):
        for target in (self.podcast, self.episode):
            with self.subTest(model=target._meta.label):
                entitlement = Entitlement(user=self.user, content_object=target)
                data = EntitlementDisplaySerializer(entitlement).data["content_object_data"]
                self.assertEqual(str(data["id"]), str(target.pk))
                self.assert_no_follower_identity(data)

    def test_generic_targets_are_opaque_without_fetching_or_stringifying_them(self):
        targets = (
            self.user,
            License(encrypted_dek_for_device=b"private-device-key"),
        )
        for target in targets:
            content_type = ContentType.objects.get_for_model(target)
            for cached_target in (False, True):
                with self.subTest(model=target._meta.label, cached=cached_target):
                    entitlement = Entitlement(
                        user=self.user, content_type=content_type, object_id=str(target.pk)
                    )
                    if cached_target:
                        entitlement.content_object = target
                    with (
                        self.assertNumQueries(0),
                        mock.patch.object(
                            type(target), "__str__", side_effect=AssertionError("Private target")
                        ),
                    ):
                        data = EntitlementDisplaySerializer(entitlement).data
                    self.assertEqual(data["content_object_data"], {"id": str(target.pk)})

    def test_public_membership_and_subscription_exclude_provider_identifiers(self):
        plan = Plan.objects.create(name="Public fan plan", tier=Plan.Level.FAN)
        membership, _ = Membership.objects.get_or_create(user=self.user)
        membership.plan = plan
        membership.save(update_fields=["plan"])
        subscription = Subscription.objects.create(
            membership=membership,
            subscription_id="private-subscription-reference",
            external_id="private-payment-provider-reference",
        )

        self.assertEqual(
            set(PlanModelSerializer(plan).data),
            {"id", "name", "features", "tier", "price_monthly", "price_annual"},
        )
        self.assertEqual(set(MembershipSerializer(membership).data), {"id", "user", "plan"})
        data = SubscriptionSerializer(subscription).data
        self.assertEqual(
            set(data),
            {
                "id",
                "membership",
                "active",
                "status",
                "start_date",
                "trial_ends",
                "end_date",
                "auto_renew",
            },
        )
        payload = json.dumps(data, default=str)
        for private_value in (
            str(membership.customer_id),
            subscription.subscription_id,
            subscription.external_id,
            self.user.email,
            self.user.clerk_user_id,
            self.user.password,
        ):
            self.assertNotIn(private_value, payload)
