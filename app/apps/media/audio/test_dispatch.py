"""Characterize database-to-worker publication without running media providers."""

from unittest import mock

from django.db import transaction
from django.test import TransactionTestCase

from apps.media.audio.models import Audio
from apps.posts.podcasts.models import Episode, Podcast


class AudioDispatchTransactionTests(TransactionTestCase):
    def setUp(self):
        podcast = Podcast.objects.create(title="Dispatch transaction fixture")
        self.episode = Episode.objects.create(podcast=podcast, title="Pending audio")

    def create_audio(self, **overrides):
        values = {
            "episode": self.episode,
            "name": "Master",
            "file": "fixtures/master.mp3",
            "quality": Audio.Quality.HIGH,
            "master": True,
        }
        values.update(overrides)
        return Audio.objects.create(**values)

    @mock.patch("apps.media.audio.receivers.process_audio.delay")
    def test_master_is_dispatched_once_only_after_outer_transaction_commits(self, delay):
        visible_at_dispatch = []
        delay.side_effect = lambda identifier: visible_at_dispatch.append(
            Audio.objects.filter(pk=identifier).exists()
        )

        with transaction.atomic():
            with transaction.atomic():
                audio = self.create_audio()
                delay.assert_not_called()
            delay.assert_not_called()
            audio.name = "Final metadata"
            audio.save(update_fields=["name"])
            delay.assert_not_called()

        delay.assert_called_once_with(str(audio.pk))
        self.assertEqual(visible_at_dispatch, [True])

    @mock.patch("apps.media.audio.receivers.process_audio.delay")
    def test_rollback_discards_audio_and_its_worker_publication(self, delay):
        with self.assertRaisesMessage(ValueError, "reject upload"), transaction.atomic():
            audio = self.create_audio()
            raise ValueError("reject upload")

        self.assertFalse(Audio.objects.filter(pk=audio.pk).exists())
        delay.assert_not_called()

    @mock.patch("apps.media.audio.receivers.process_audio.delay")
    def test_rolled_back_savepoint_does_not_discard_later_valid_publication(self, delay):
        with transaction.atomic():
            with (
                self.assertRaisesMessage(ValueError, "discard first attempt"),
                transaction.atomic(),
            ):
                discarded = self.create_audio()
                raise ValueError("discard first attempt")
            accepted = self.create_audio()
            delay.assert_not_called()

        self.assertFalse(Audio.objects.filter(pk=discarded.pk).exists())
        delay.assert_called_once_with(str(accepted.pk))

    @mock.patch("apps.media.audio.receivers.process_audio.delay")
    def test_derived_or_already_processed_audio_does_not_start_another_pipeline(self, delay):
        with transaction.atomic():
            self.create_audio(master=False, quality=Audio.Quality.PREVIEW)
            self.create_audio(processed=True)

        delay.assert_not_called()
