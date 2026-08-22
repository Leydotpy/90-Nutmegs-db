import logging
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.core.files.storage import default_storage

s3 = boto3.client(
    "s3",
    aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY"),
    region_name=getattr(settings, "AWS_REGION"),
)

BUCKET = getattr(settings, "MEDIA_BUCKET")  # e.g. "my-podcast-bucket"

logger = logging.getLogger(__name__)


def cleanup_storage_keys(keys: list):
    """
    Delete a list of storage keys (paths) using default_storage.
    Continue deleting remaining keys even if some deletions fail; log exceptions.
    """
    for key in keys:
        try:
            if key and default_storage.exists(key):
                default_storage.delete(key)
        except Exception as exc:
            logger.warning("Failed to delete storage key %s: %s", key, exc)


def upload_fileobj_to_s3(fileobj, key, content_type=None, acl="private"):
    extra_args = {"ACL": acl}
    if content_type:
        extra_args["ContentType"] = content_type
    s3.upload_fileobj(
        Fileobj=fileobj,
        Bucket=BUCKET,
        Key=key,
        ExtraArgs=extra_args
    )
    return f"s3://{BUCKET}/{key}"


def generate_presigned_get_url(key, expires_in=3600):
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError:
        return None


def generate_presigned_put_url(key, expires_in=3600, content_type=None):
    params = {"Bucket": BUCKET, "Key": key}
    if content_type:
        params["ContentType"] = content_type
    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in
        )
        return url
    except ClientError:
        return None


def generate_presigned_url_for_name(storage, name: str, expires_in: int = 3600):
    """
    Return a presigned GET URL for `name` using a django-storages S3 backend if possible,
    otherwise fall back to storage.url(name) if available.
    """
    try:
        public_url = storage.url(name)
    except Exception:
        public_url = None

    # If URL looks public (no query params) return it
    if public_url and ("?" not in public_url):
        return public_url

    backend_cls_name = storage.__class__.__name__
    if backend_cls_name == "S3Boto3Storage":
        try:
            # try to get the internal boto3 client from storage
            s3_client = storage.connection.meta.client
        except Exception:
            # fallback: build client from settings/environment
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
                aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
                region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
                endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
            )

        bucket_name = getattr(storage, "bucket_name", None) or getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": name},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as exc:
            logger.exception("Failed to generate presigned URL via boto3: %s", exc)
            return public_url

    # Non-S3 backend: return public_url (if present) or None
    return public_url


def _rsa_signer(private_key_pem: str, message: bytes) -> bytes:
    """
    Sign bytes using RSA private key PEM using PKCS1v15 + SHA1 (CloudFront expects SHA1).
    Return signature bytes.
    """
    private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())
    return signature


def generate_cloudfront_signed_cookies(resource_url: str, key_pair_id: str, private_key_pem: str,
                                       expires_in_seconds: int = 900):
    """
    Generate CloudFront signed cookies granting access to resource_url until expires_in_seconds from now.
    resource_url can be a wildcard pattern (e.g. https://<domain>/<prefix>/*)

    Returns: dict { "cookies": {...}, "expires_at": datetime }
    cookies keys are: 'CloudFront-Policy', 'CloudFront-Signature', 'CloudFront-Key-Pair-Id'
    """

    expires = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
    # Build a canned policy for this resource
    policy = (
            '{"Statement":[{"Resource":"%s","Condition":{"DateLessThan":{"AWS:EpochTime":%d}}}]}' % (resource_url,
                                                                                                     int(expires.timestamp()))
    )

    try:
        signer = CloudFrontSigner(key_pair_id, lambda message: _rsa_signer(private_key_pem, message))
        cookies = signer.generate_presigned_cookie(policy=policy)
        # cookies is a dict with cookie values
        return {"cookies": cookies, "expires_at": expires}
    except Exception as exc:
        logger.exception("Failed to generate CloudFront signed cookies: %s", exc)
        raise
