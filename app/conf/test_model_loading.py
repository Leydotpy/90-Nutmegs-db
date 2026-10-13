"""Compatibility at the runtime model lookup boundaries migrated in SF-04."""

from apps.media.models import PlayList
from apps.posts.podcasts.models import Episode, Podcast
from apps.queue.models import Queue
from core.validators import ExtendedURLValidator
from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase


class RuntimeModelLookupTests(TestCase):
    def test_queue_resolves_existing_model_labels_and_missing_items(self):
        podcast = Podcast.objects.create(title="Registry lookup")
        episode = Episode.objects.create(podcast=podcast, title="Episode lookup")
        playlist = PlayList.objects.create(name="Playlist lookup")

        for item, label in (
            (podcast, "podcasts.Podcast"),
            (episode, "podcasts.Episode"),
            (playlist, "media.Playlist"),
            (playlist, "media.PlayList"),
        ):
            with self.subTest(label=label), self.assertNumQueries(1):
                self.assertEqual(Queue._get_item(str(item.pk), label), item)

        deleted_id = str(episode.pk)
        episode.delete()
        with self.assertRaises(Http404):
            Queue._get_item(deleted_id, "podcasts.Episode")

    def test_local_url_validator_falls_back_to_canonical_flatpage_model(self):
        FlatPage.objects.create(url="/terms-for-model-lookup/", title="Terms", content="Terms")

        with self.assertNumQueries(1):
            ExtendedURLValidator()("/terms-for-model-lookup/")
        with self.assertRaises(ValidationError):
            ExtendedURLValidator()("/missing-terms-for-model-lookup/")

    def test_local_url_validator_resolves_regular_routes_without_model_queries(self):
        with self.assertNumQueries(0):
            ExtendedURLValidator()("/health/live/")
