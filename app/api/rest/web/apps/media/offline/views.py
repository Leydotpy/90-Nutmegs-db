import base64
import logging
import secrets
from datetime import timedelta

import boto3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.rest.web.apps.media.offline.serializers import DeviceRegisterSerializer, OfflineRequestSerializer
from apps.media.offline.models import Device, License, Package, Packaging
from apps.media.offline.tasks import build_offline_package_task, get_package_status
from apps.media.storage import generate_presigned_url_for_name

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_offline_license(request, package_id):
    """
    Client sends:
      - device_id (unique per-install)
    """
    device_id = request.data.get("device_id")
    package = get_object_or_404(Package, pk=package_id)
    device = get_object_or_404(Device, device_id=device_id, user=request.user)
    # encrypted_dek is the KMS-encrypted DEK. For device wrapping we need plaintext DEK.
    # Option A: ask KMS to decrypt the encrypted_dek then encrypt with device public key (will require server KMS decrypt permission).
    kms_client = boto3.client("kms")
    resp = kms_client.decrypt(CiphertextBlob=package.encrypted_dek)
    plaintext_dek = resp["Plaintext"]
    # encrypt plaintext_dek to device public key
    public_key = serialization.load_pem_public_key(device.public_key_pem.encode())
    wrapped = public_key.encrypt(plaintext_dek,
                                 padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(),
                                              label=None))
    # Create license record with expiry
    expires_at = timezone.now() + timedelta(days=7)
    lic = License.objects.create(
        package=package,
        user=request.user,
        device_id=device_id,
        encrypted_dek_for_device=wrapped,
        issued_at=timezone.now(),
        expires_at=expires_at
    )
    # Return presigned download URL for package + encrypted DEK payload (optional)
    s3 = boto3.client("s3")
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    presigned = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": package.storage_key},
                                          ExpiresIn=3600)
    return Response({
        "license_id": str(lic.id),
        "download_url": presigned,
        "expires_at": expires_at.isoformat(),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device(request):
    """
    Register / update a device. Client provides device_id, public_key_pem, device_type, name, etc.
    """
    serializer = DeviceRegisterSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    device = serializer.save()
    return Response({"device_id": device.device_id, "id": str(device.id)}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_offline_package(request):
    """
    Request offline package for episode.
    Flow:
      - validate entitlement (episode.offline_allowed, user subscription/tier, user setting for offline downloads)
      - check device exists and not revoked
      - if package exists -> create license and return presigned url + wrapped dek
      - else enqueue packaging task (returns task_id), and return job status endpoint
    """
    serializer = OfflineRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user
    episode = serializer.validated_data["episode"]
    preset = serializer.validated_data["preset"]
    device_id = serializer.validated_data["device_id"]
    days_valid = serializer.validated_data["days_valid"]
    max_plays = serializer.validated_data.get("max_plays")

    # entitlement checks
    if not episode.offline_allowed:
        return Response({"detail": "Offline download disabled for this episode"}, status=403)

    # check user's plan / entitlement - adapt to your policy
    def user_has_offline_entitlement(u, episode):
        # Example: episode.access_tier vs user's plan slug; or global user setting
        try:
            plan = u.transcription_quota.plan
            if getattr(plan, "can_download_high_quality", False):
                return True
        except Exception:
            pass
        # fall back: if episode is free
        if getattr(episode, "is_free", False):
            return True
        return False

    if not user_has_offline_entitlement(user, episode):
        return Response({"detail": "Your subscription does not allow offline downloads for this episode"}, status=403)

    # find device
    try:
        device = Device.objects.get(user=user, device_id=device_id, revoked=False)
    except Device.DoesNotExist:
        return Response({"detail": "Device not registered or revoked"}, status=404)

    # check per-user/device offline capacity (example checks)
    if device.max_offline_items:
        existing_count = License.objects.filter(device=device, revoked=False,
                                                expires_at__gt=settings.NOW()).count() if hasattr(settings,
                                                                                                  "NOW") else License.objects.filter(
            device=device, revoked=False).count()
        if existing_count >= device.max_offline_items:
            return Response({"detail": "Device offline item limit reached"}, status=403)

    # Attempt to reuse existing package for same episode + preset
    existing_pkg = Package.objects.filter(episode=episode, preset=preset).order_by("-created_at").first()
    if existing_pkg:
        # create license synchronously and return wrapped DEK + presigned URL
        lic = _create_license_for_device(existing_pkg, user, device, days_valid=days_valid, max_plays=max_plays)
        url = _package_presigned_url(existing_pkg)
        return Response({
            "license_id": str(lic.id),
            "download_url": url,
            "encrypted_dek_for_device": base64.b64encode(lic.encrypted_dek_for_device).decode("utf-8"),
            "expires_at": lic.expires_at,
        }, status=201)

    # else create PackagingJob and enqueue
    callback_url = request.data.get("callback_url")  # optional
    webhook_secret = None
    if callback_url:
        webhook_secret = secrets.token_urlsafe(32)[:64]  # store secret for signing

    job = Packaging.objects.create(
        episode=episode,
        user=user,
        preset=preset,
        status=Packaging.STATUS_PENDING,
        callback_url=callback_url,
        webhook_secret=webhook_secret
    )

    # else: create a packaging job
    # packaging task will call build_offline_package_streaming(...) and create OfflinePackage row
    task = build_offline_package_task.apply_async(args=(str(job.id),))
    job.task_id = task.id
    job.save(update_fields=["task_id"])
    return Response({
        "detail": "Packaging started",
        "task_id": task.id,
        "status_url": f"/api/offline/packages/status/{task.id}/"
    }, status=202)


def _create_license_for_device(pkg: Package, user, device: Device, days_valid: int = 7,
                               max_plays: int = None) -> License:
    """
    Decrypt package.encrypted_dek with KMS then wrap with device public key and create OfflineLicense.
    WARNING: server performs KMS.Decrypt and handles plaintext DEK briefly - restrict service to trusted environment.
    """
    kms = boto3.client("kms",
                       aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
                       aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
                       region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
                       endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None))
    dec = kms.decrypt(CiphertextBlob=bytes(pkg.encrypted_dek))
    plaintext_dek = dec["Plaintext"]

    # wrap plaintext_dek with device public key PEM
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding as asympadding

    pubkey = serialization.load_pem_public_key(device.public_key_pem.encode())
    wrapped = pubkey.encrypt(
        plaintext_dek,
        asympadding.OAEP(mgf=asympadding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

    expires_at = timezone.now() + timedelta(days=days_valid)
    lic = License.objects.create(
        package=pkg, user=user, device=device,
        encrypted_dek_for_device=wrapped,
        expires_at=expires_at, max_plays=max_plays
    )
    # best-effort zero plaintext_dek
    plaintext_dek = None
    return lic


def _package_presigned_url(pkg: Package):
    storage = default_storage
    key = pkg.storage_key
    url = generate_presigned_url_for_name(storage, key, expires_in=getattr(settings, "PRESIGN_EXPIRES_SECONDS", 3600))
    return url


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def packaging_status(request, task_id):
    """
    Poll for packaging status. Returns:
      - status: pending | success | failed
      - package_id (if success)
      - error (if failed)
    """
    status_info = get_package_status(task_id)
    return Response(status_info)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_license(request, license_id):
    lic = get_object_or_404(License, pk=license_id, user=request.user)
    lic.revoked = True
    lic.save(update_fields=["revoked"])
    return Response({"status": "revoked"})
