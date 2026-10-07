from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.media.canonical import MediaAccessClass, MediaAsset, MediaLocation
from apps.media.providers.contracts import MediaProviderError, ObjectMetadata
from apps.media.upload_finalization import (
    R2FinalizationRequest,
    R2UploadFinalizer,
    UploadFinalizationRejected,
)


class R2UploadFinalizerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="upload-owner",
            email="upload-owner@example.test",
            clerk_user_id="clerk-upload-owner",
        )
        self.asset = MediaAsset.objects.create(
            created_by=self.user,
            media_type=MediaAsset.MediaType.AUDIO,
            mime_type="audio/mpeg",
            byte_size=1024,
        )
        self.private_objects = mock.Mock()
        self.finalizer = R2UploadFinalizer(
            private_object_storage=self.private_objects,
            private_container="sanfootball-private",
            max_upload_bytes=2048,
        )
        self.request = R2FinalizationRequest(
            asset_id=self.asset.pk,
            key=f"temporary/uploads/{self.asset.pk.hex}/session.mp3",
        )
        self.private_objects.head.return_value = ObjectMetadata(
            resource_id=self.request.key,
            byte_size=1024,
            etag='"source-etag"',
            content_type="audio/mpeg",
        )
        self.private_objects.promote.side_effect = self.promoted_object

    @staticmethod
    def promoted_object(*, destination_key, **_kwargs):
        return ObjectMetadata(
            resource_id=destination_key,
            byte_size=1024,
            etag='"canonical-etag"',
            content_type="audio/mpeg",
        )

    def test_valid_object_is_promoted_and_available_idempotently(self):
        first = self.finalizer.finalize(self.request, actor=self.user)
        second = self.finalizer.finalize(self.request, actor=self.user)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(MediaLocation.objects.count(), 1)
        self.assertEqual(first.container, "sanfootball-private")
        self.assertTrue(first.locator.startswith(f"canonical/audio/{self.asset.pk.hex}/"))
        self.assertNotEqual(first.locator, self.request.key)
        self.assertTrue(first.is_primary)
        self.private_objects.promote.assert_called_once()
        self.private_objects.head.assert_called_once_with(key=self.request.key)
        self.assertEqual(
            self.private_objects.delete.call_args_list,
            [mock.call(key=self.request.key), mock.call(key=self.request.key)],
        )
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.UPLOADED)

    def test_duplicate_finalization_cannot_start_a_second_promotion(self):
        duplicate_error = None

        def promote_while_duplicate_arrives(*, destination_key, **kwargs):
            nonlocal duplicate_error
            try:
                self.finalizer.finalize(self.request, actor=self.user)
            except UploadFinalizationRejected as exc:
                duplicate_error = exc
            return self.promoted_object(destination_key=destination_key, **kwargs)

        self.private_objects.promote.side_effect = promote_while_duplicate_arrives

        location = self.finalizer.finalize(self.request, actor=self.user)

        self.assertIsNotNone(duplicate_error)
        self.assertIn("already in progress", str(duplicate_error))
        self.assertEqual(self.private_objects.promote.call_count, 1)
        self.assertEqual(location.status, MediaLocation.Status.AVAILABLE)
        self.assertEqual(MediaLocation.objects.count(), 1)

    def test_same_etag_sessions_use_distinct_destinations_and_cannot_overwrite(self):
        second_request = R2FinalizationRequest(
            asset_id=self.asset.pk,
            key=f"temporary/uploads/{self.asset.pk.hex}/second-session.mp3",
        )
        promoted_keys = []
        nested_location = None
        nested = False

        def head_for_session(*, key):
            return ObjectMetadata(
                resource_id=key,
                byte_size=1024,
                etag='"source-etag"',
                content_type="audio/mpeg",
            )

        def promote_with_slower_first_copy(*, destination_key, **kwargs):
            nonlocal nested, nested_location
            promoted_keys.append(destination_key)
            if not nested:
                nested = True
                nested_location = self.finalizer.finalize(second_request, actor=self.user)
            return self.promoted_object(destination_key=destination_key, **kwargs)

        self.private_objects.head.side_effect = head_for_session
        self.private_objects.promote.side_effect = promote_with_slower_first_copy

        returned_location = self.finalizer.finalize(self.request, actor=self.user)

        self.assertIsNotNone(nested_location)
        self.assertEqual(returned_location.pk, nested_location.pk)
        self.assertEqual(len(promoted_keys), 2)
        self.assertNotEqual(promoted_keys[0], promoted_keys[1])
        losing_reservation = MediaLocation.objects.get(locator=promoted_keys[0])
        self.assertEqual(losing_reservation.status, MediaLocation.Status.FAILED)
        self.assertEqual(
            losing_reservation.metadata["promotion_state"],
            "superseded",
        )
        self.assertEqual(nested_location.locator, promoted_keys[1])

    def test_public_asset_still_finalizes_as_a_private_source(self):
        self.asset.access_class = MediaAccessClass.PUBLIC
        self.asset.save(update_fields=("access_class", "updated_at"))

        location = self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.head.assert_called_once_with(key=self.request.key)
        self.private_objects.promote.assert_called_once_with(
            source_container="sanfootball-private",
            source_key=self.request.key,
            destination_key=location.locator,
            source_etag='"source-etag"',
            content_type="audio/mpeg",
        )
        self.private_objects.delete.assert_called_once_with(key=self.request.key)
        self.assertEqual(location.container, "sanfootball-private")

    def test_creatorless_asset_is_rejected_before_provider_call(self):
        self.asset.created_by = None
        self.asset.save(update_fields=("created_by", "updated_at"))

        with self.assertRaisesMessage(UploadFinalizationRejected, "not available"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.head.assert_not_called()

    def test_wrong_creator_is_rejected_before_provider_call(self):
        other_user = get_user_model().objects.create_user(
            username="another-upload-user",
            email="another-upload-user@example.test",
            clerk_user_id="clerk-another-upload-user",
        )

        with self.assertRaisesMessage(UploadFinalizationRejected, "not available"):
            self.finalizer.finalize(self.request, actor=other_user)

        self.private_objects.head.assert_not_called()

    def test_wrong_key_is_rejected_before_provider_call(self):
        request = R2FinalizationRequest(
            asset_id=self.request.asset_id,
            key="temporary/uploads/another-asset/session.mp3",
        )

        with self.assertRaisesMessage(UploadFinalizationRejected, "key"):
            self.finalizer.finalize(request, actor=self.user)

        self.private_objects.head.assert_not_called()

    def test_size_mismatch_is_deleted_and_asset_fails(self):
        self.private_objects.head.return_value = ObjectMetadata(
            resource_id=self.request.key,
            byte_size=2049,
            etag='"source-etag"',
            content_type="audio/mpeg",
        )

        with self.assertRaisesMessage(UploadFinalizationRejected, "size"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.delete.assert_called_once_with(key=self.request.key)
        self.private_objects.promote.assert_not_called()
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.FAILED)

    def test_content_type_mismatch_is_deleted(self):
        self.private_objects.head.return_value = ObjectMetadata(
            resource_id=self.request.key,
            byte_size=1024,
            etag='"source-etag"',
            content_type="application/octet-stream",
        )

        with self.assertRaisesMessage(UploadFinalizationRejected, "content type"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.delete.assert_called_once_with(key=self.request.key)

    def test_declared_checksum_without_trusted_provider_proof_is_rejected(self):
        self.asset.checksum = "a" * 64
        self.asset.save(update_fields=("checksum", "updated_at"))

        with self.assertRaisesMessage(UploadFinalizationRejected, "trusted checksum"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.promote.assert_not_called()
        self.private_objects.delete.assert_called_once_with(key=self.request.key)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.FAILED)

    def test_ready_retry_returns_existing_location_without_destructive_revalidation(self):
        first = self.finalizer.finalize(self.request, actor=self.user)
        self.asset.status = MediaAsset.Status.READY
        self.asset.save(update_fields=("status", "updated_at"))
        self.private_objects.head.reset_mock()
        self.private_objects.head.return_value = ObjectMetadata(
            resource_id=self.request.key,
            byte_size=99,
            etag='"changed-etag"',
            content_type="application/octet-stream",
        )

        second = self.finalizer.finalize(self.request, actor=self.user)

        second.refresh_from_db()
        self.asset.refresh_from_db()
        self.assertEqual(first.pk, second.pk)
        self.assertTrue(second.is_primary)
        self.assertEqual(self.asset.status, MediaAsset.Status.READY)
        self.private_objects.head.assert_not_called()

    def test_cleanup_failure_still_marks_asset_failed(self):
        self.private_objects.head.return_value = ObjectMetadata(
            resource_id=self.request.key,
            byte_size=2049,
            etag='"source-etag"',
            content_type="audio/mpeg",
        )
        self.private_objects.delete.side_effect = RuntimeError("cleanup failed")

        with self.assertRaisesMessage(RuntimeError, "cleanup failed"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.FAILED)

    def test_deleted_asset_is_rejected_before_provider_call(self):
        self.asset.status = MediaAsset.Status.DELETED
        self.asset.save(update_fields=("status", "updated_at"))

        with self.assertRaisesMessage(UploadFinalizationRejected, "Deleted"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.head.assert_not_called()

    def test_ready_asset_without_canonical_location_is_not_touched(self):
        self.asset.status = MediaAsset.Status.READY
        self.asset.save(update_fields=("status", "updated_at"))

        with self.assertRaisesMessage(UploadFinalizationRejected, "not accepting"):
            self.finalizer.finalize(self.request, actor=self.user)

        self.private_objects.head.assert_not_called()
        self.private_objects.delete.assert_not_called()

    def test_competing_session_keeps_a_durable_failed_reservation_for_cleanup(self):
        winner_key = f"canonical/audio/{self.asset.pk.hex}/winner.mp3"

        def promote_after_competing_completion(*, destination_key, **kwargs):
            MediaLocation.objects.create(
                asset=self.asset,
                provider=MediaLocation.Provider.CLOUDFLARE,
                product=MediaLocation.Product.R2,
                container="sanfootball-private",
                locator=winner_key,
                status=MediaLocation.Status.AVAILABLE,
                is_primary=True,
            )
            MediaAsset.objects.filter(pk=self.asset.pk).update(status=MediaAsset.Status.UPLOADED)
            return self.promoted_object(destination_key=destination_key, **kwargs)

        self.private_objects.promote.side_effect = promote_after_competing_completion

        location = self.finalizer.finalize(self.request, actor=self.user)

        promoted_key = self.private_objects.promote.call_args.kwargs["destination_key"]
        self.assertEqual(location.locator, winner_key)
        self.private_objects.delete.assert_called_once_with(key=self.request.key)
        losing_reservation = MediaLocation.objects.get(locator=promoted_key)
        self.assertEqual(losing_reservation.status, MediaLocation.Status.FAILED)
        self.assertEqual(
            losing_reservation.metadata["promotion_state"],
            "superseded",
        )

    def test_status_change_during_promotion_leaves_a_durable_pending_reservation(self):
        def promote_after_status_change(*, destination_key, **kwargs):
            MediaAsset.objects.filter(pk=self.asset.pk).update(status=MediaAsset.Status.READY)
            return self.promoted_object(destination_key=destination_key, **kwargs)

        self.private_objects.promote.side_effect = promote_after_status_change

        with self.assertRaisesMessage(UploadFinalizationRejected, "not accepting"):
            self.finalizer.finalize(self.request, actor=self.user)

        promoted_key = self.private_objects.promote.call_args.kwargs["destination_key"]
        self.private_objects.delete.assert_not_called()
        reservation = MediaLocation.objects.get(
            container="sanfootball-private",
            locator=promoted_key,
        )
        self.assertEqual(reservation.status, MediaLocation.Status.PENDING)
        self.assertEqual(reservation.metadata["temporary_key"], self.request.key)

    def test_upload_declaration_change_during_promotion_is_rejected(self):
        def promote_after_declaration_change(*, destination_key, **kwargs):
            MediaAsset.objects.filter(pk=self.asset.pk).update(mime_type="application/octet-stream")
            return self.promoted_object(destination_key=destination_key, **kwargs)

        self.private_objects.promote.side_effect = promote_after_declaration_change

        with self.assertRaisesMessage(UploadFinalizationRejected, "declaration changed"):
            self.finalizer.finalize(self.request, actor=self.user)

        promoted_key = self.private_objects.promote.call_args.kwargs["destination_key"]
        self.private_objects.delete.assert_not_called()
        reservation = MediaLocation.objects.get(locator=promoted_key)
        self.assertEqual(reservation.status, MediaLocation.Status.PENDING)

    def test_provider_failure_after_reservation_remains_reconcilable(self):
        self.private_objects.promote.side_effect = MediaProviderError(
            "copy outcome unknown",
            provider="cloudflare",
            operation="r2.copy_object",
            retryable=True,
        )

        with self.assertRaises(MediaProviderError):
            self.finalizer.finalize(self.request, actor=self.user)

        reservation = MediaLocation.objects.get(status=MediaLocation.Status.PENDING)
        self.assertEqual(reservation.metadata["promotion_state"], "promoting")
        self.assertEqual(reservation.metadata["temporary_key"], self.request.key)
        self.private_objects.delete.assert_not_called()

    def test_invalid_promoted_metadata_marks_reservation_and_asset_failed(self):
        self.private_objects.promote.return_value = ObjectMetadata(
            resource_id="wrong-destination",
            byte_size=2048,
            etag='"canonical-etag"',
            content_type="audio/mpeg",
        )
        self.private_objects.promote.side_effect = None

        with self.assertRaises(UploadFinalizationRejected):
            self.finalizer.finalize(self.request, actor=self.user)

        reservation = MediaLocation.objects.get()
        self.assertEqual(reservation.status, MediaLocation.Status.FAILED)
        self.assertEqual(reservation.metadata["promotion_state"], "failed")
        self.private_objects.delete.assert_called_once_with(key=self.request.key)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, MediaAsset.Status.FAILED)
