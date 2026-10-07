import json
import logging
import os
import shutil
import struct
import tempfile
import uuid
from datetime import datetime

import boto3
from celery import shared_task
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings

from apps.media.offline.models import Packaging
from apps.media.offline.webhook import send_signed_webhook

# optional: Django Channels
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    CHANNELS_AVAILABLE = True
except Exception:
    CHANNELS_AVAILABLE = False

logger = logging.getLogger(__name__)

from apps.media.audio.models import Audio
from apps.media.offline.models import Package

# Tunable chunk size (64 KB is a reasonable trade-off)
CHUNK_SIZE = 64 * 1024

# Package file magic + version
MAGIC = b"PODPKG1v1"  # 8 bytes

# Helpers to pack/unpack integers
_pack_u32 = lambda v: struct.pack(">I", v)
_unpack_u32 = lambda b: struct.unpack(">I", b)[0]
_pack_u16 = lambda v: struct.pack(">H", v)
_unpack_u16 = lambda b: struct.unpack(">H", b)[0]
_pack_u64 = lambda v: struct.pack(">Q", v)
_unpack_u64 = lambda b: struct.unpack(">Q", b)[0]

# KMS + S3 clients (reuse; boto3 uses env/config for credentials)
_kms = boto3.client(
    "kms",
    aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
    region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
    endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
)
_s3 = boto3.client(
    "s3",
    aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
    region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
    endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
)

# For mapping celery task id -> result/package id, we can use cache or a DB Job model. For simplicity use cache.
from django.core.cache import cache


def get_package_status(task_id: str):
    info = cache.get(f"offline_pkg_task:{task_id}")
    if info:
        return info
    # if not in cache, unknown or finished long ago
    return {"status": "unknown"}


def _derive_keys_from_dek(dek: bytes, info: bytes = b"podcast-offline-package", length: int = 64):
    """
    Use HKDF-SHA256 to expand DEK into `length` bytes, then split into enc_key and mac_key.
    We choose length=64 -> enc_key=32 (AES-256), mac_key=32 (HMAC-SHA256).
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    okm = hkdf.derive(dek)  # bytes
    enc_key = okm[:32]
    mac_key = okm[32:64]
    return enc_key, mac_key


@shared_task(bind=True)
def build_offline_package_streaming(self, episode_id: str, user_id: int = None, kms_cmk_id: str = None,
                                    expiry_days: int = 7):
    """
    Streaming encryption packaging:
      - downloads master audio chunk-by-chunk,
      - transcodes if needed (here we assume master audio is already usable; optional ffmpeg transform),
      - generates DEK with KMS (GenerateDataKey),
      - derives enc/mac keys via HKDF,
      - encrypts file in CHUNK_SIZE blocks using AES-CTR + per-chunk HMAC-SHA256,
      - writes package to tmp file without ever loading entire file into memory,
      - uploads package to S3 and creates OfflinePackage row storing encrypted DEK (CiphertextBlob).
    """
    if not getattr(settings, "CUSTOM_OFFLINE_DRM_ENABLED", False):
        raise RuntimeError("Offline packaging is disabled")

    tmpdir = tempfile.mkdtemp(prefix=f"offline-{episode_id}-")
    try:
        # find master audio (adjust to your Audio query API)
        audio = Audio.objects.master(episode_id=episode_id)
        if audio is None:
            raise RuntimeError(f"No master audio for episode {episode_id}")

        # download master to local temp file (streaming write)
        master_local = os.path.join(tmpdir, "master")
        with open(master_local, "wb") as mf:
            for chunk in audio.file.chunks():
                mf.write(chunk)

        # (Optional) you may transcode here into a consistent container (fMP4/MP3).
        # For simplicity, we use the master file as-is. If you need ffmpeg transcode, do it here.

        # 1) Generate data key from KMS (plaintext + encrypted DEK)
        cmk = kms_cmk_id or getattr(settings, "OFFLINE_KMS_CMK_ID", None)
        if not cmk:
            raise RuntimeError("KMS CMK id not configured (OFFLINE_KMS_CMK_ID)")

        # GenerateDataKey returns Plaintext (bytes) and CiphertextBlob (bytes)
        kms_resp = _kms.generate_data_key(KeyId=cmk, KeySpec="AES_256")
        plaintext_dek = kms_resp["Plaintext"]  # bytes (32)
        encrypted_dek = kms_resp["CiphertextBlob"]  # bytes; store this (BinaryField)

        # 2) derive enc_key & mac_key via HKDF
        enc_key, mac_key = _derive_keys_from_dek(plaintext_dek)

        # create random 8-byte iv_prefix (so nonce per chunk = iv_prefix (8) || counter (8))
        iv_prefix = os.urandom(8)

        # create package file
        pkg_local = os.path.join(tmpdir, "package.bin")
        with open(pkg_local, "wb") as pkgf:
            # write header
            pkgf.write(MAGIC)  # 8 bytes magic

            # manifest placeholder: we write manifest JSON afterward length-prefixing it.
            manifest = {
                "episode_id": str(episode_id),
                "created_at": datetime.utcnow().isoformat() + "Z",
                "chunk_size": CHUNK_SIZE,
                "encryption": "AES-CTR+HMAC-SHA256",
                "hkdf_info": "podcast-offline-package",
                "hkdf_salt": None,
                "iv_prefix_len": len(iv_prefix),
            }
            manifest_bytes = json.dumps(manifest).encode("utf-8")
            pkgf.write(_pack_u32(len(manifest_bytes)))
            pkgf.write(manifest_bytes)

            # write iv_prefix (fixed 8 bytes)
            pkgf.write(iv_prefix)

            # Now stream-encrypt source file by chunk
            chunk_index = 0
            with open(master_local, "rb") as src:
                while True:
                    chunk = src.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    # build 16-byte IV: iv_prefix (8 bytes) || chunk_index (8 bytes BE)
                    iv = iv_prefix + chunk_index.to_bytes(8, "big")

                    # AES-CTR encrypt: use Cipher with enc_key and iv
                    cipher = Cipher(algorithms.AES(enc_key), modes.CTR(iv))
                    encryptor = cipher.encryptor()
                    ct = encryptor.update(chunk) + encryptor.finalize()

                    # compute HMAC over (chunk_index || iv || ct)
                    h = hmac.HMAC(mac_key, hashes.SHA256())
                    h.update(chunk_index.to_bytes(8, "big"))
                    h.update(iv)
                    h.update(ct)
                    tag = h.finalize()  # 32 bytes

                    # write chunk header: chunk_index (8) | iv_len (2) | iv | ct_len (4) | ct | tag_len (2) | tag
                    pkgf.write(_pack_u64(chunk_index))
                    pkgf.write(_pack_u16(len(iv)))
                    pkgf.write(iv)
                    pkgf.write(_pack_u32(len(ct)))
                    pkgf.write(ct)
                    pkgf.write(_pack_u16(len(tag)))
                    pkgf.write(tag)

                    chunk_index += 1

        # At this point, the package file contains manifest + encrypted chunks

        # 3) upload package to S3 (you can switch to multipart streaming upload for large objects)
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
        # object key pattern
        key = f"offline/packages/{episode_id}/{uuid.uuid4().hex}.pkg"
        _s3.upload_file(pkg_local, bucket, key)

        # 4) save OfflinePackage DB row (store encrypted_dek)
        size_bytes = os.path.getsize(pkg_local)
        pkg_row = Package.objects.create(
            episode_id=episode_id,
            created_by_id=user_id,
            storage_key=key,
            encrypted_dek=encrypted_dek,
            kms_key_id=cmk,
            size_bytes=size_bytes,
            manifest=manifest,
        )

        # Zero sensitive plaintext variables as best-effort (can't guarantee memory purge in Python)
        plaintext_dek = None
        enc_key = None
        mac_key = None

        return str(pkg_row.id)

    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            logger.debug("Failed to cleanup tmpdir", exc_info=True)


@shared_task(bind=True)
def build_offline_package_task(self, job_id: str):
    """
    Celery task that picks a PackagingJob, runs package building, updates job,
    sends webhook and websocket message on completion/failure.
    """
    try:
        job = Packaging.objects.get(pk=job_id)
    except Packaging.DoesNotExist:
        logger.error("PackagingJob not found: %s", job_id)
        return {"status": "unknown"}

    if not getattr(settings, "CUSTOM_OFFLINE_DRM_ENABLED", False):
        logger.warning("Rejected disabled offline packaging job %s", job_id)
        job.mark_failed("Offline packaging is disabled")
        return {"status": "disabled"}

    job.mark_running(task_id=self.request.id)
    try:
        # call the streaming packer (it should create OfflinePackage DB row)
        # The packer earlier returned the created OfflinePackage.id (string)
        package_id = build_offline_package_streaming.__wrapped__(None, str(job.episode.id),
                                                                 user_id=(job.user.id if job.user else None),
                                                                 kms_cmk_id=getattr(settings, "OFFLINE_KMS_CMK_ID",
                                                                                    None))
        # load package
        from apps.media.offline.models import Package
        package = Package.objects.get(pk=package_id)
        job.mark_success(package)

        # prepare payload
        payload = {
            "job_id": str(job.id),
            "status": "success",
            "package_id": str(package.id),
            "episode_id": str(job.episode.id),
            "preset": job.preset,
            "package_storage_key": package.storage_key,
        }

        # send webhook if present
        if job.callback_url and job.webhook_secret:
            try:
                send_signed_webhook(job.callback_url, payload, job.webhook_secret)
            except Exception:
                logger.exception("Failed sending webhook for job %s", job.id)

        # send websocket via channels if enabled
        if CHANNELS_AVAILABLE:
            try:
                channel_layer = get_channel_layer()
                group = f"user_{job.user.id}" if job.user else None
                if group:
                    async_to_sync(channel_layer.group_send)(group,
                                                            {"type": "offline.package.ready", "payload": payload})
            except Exception:
                logger.exception("Channels notify failed for job %s", job.id)

        return {"status": "success", "package_id": package_id}

    except Exception as exc:
        logger.exception("Packaging failed for job %s: %s", job_id, exc)
        job.mark_failed(str(exc))
        payload = {"job_id": str(job.id), "status": "failed", "error": str(exc)}
        if job.callback_url and job.webhook_secret:
            try:
                send_signed_webhook(job.callback_url, payload, job.webhook_secret)
            except Exception:
                logger.exception("Failed sending failure webhook for job %s", job.id)
        if CHANNELS_AVAILABLE and job.user:
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(f"user_{job.user.id}",
                                                        {"type": "offline.package.failed", "payload": payload})
            except Exception:
                logger.exception("Channels notify failed for job %s", job.id)
        raise
