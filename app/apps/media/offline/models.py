import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.compat import get_user_model


User = get_user_model()


def offline_upload_to(instance, filename):
    return f"offline/pkg/{instance.episode.id}/{instance.user.username}/{filename}"


class Package(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True, editable=False)
    episode = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE, related_name="offline_packages")
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    storage_key = models.CharField(max_length=1024)   # S3 key of encrypted package
    encrypted_dek = models.BinaryField()              # DEK encrypted under KMS CMK (or re-wrapped)
    kms_key_id = models.CharField(max_length=256, null=True, blank=True)  # KMS CMK id used
    size_bytes = models.BigIntegerField(null=True, blank=True)
    file = models.FileField(upload_to=offline_upload_to, null=True, blank=True)
    manifest = models.JSONField(default=dict, blank=True)  # metadata (length, bitrate)
    created_at = models.DateTimeField(auto_now_add=True)

    preset = models.CharField(max_length=32, default="default")  # e.g. preview/medium/high

    class Meta:
        indexes = [
            models.Index(fields=["episode", "preset"]),
        ]

    def __str__(self):
        return f"OfflinePackage({self.episode.id}, preset={self.preset})"



class License(models.Model):
    """
    Per-device license for an offline <Package> model, binds encrypted_dek to a device/public-key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="licenses")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    encrypted_dek_for_device = models.BinaryField()           # DEK encrypted with device public key
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()                       # offline expiry
    max_plays = models.IntegerField(null=True, blank=True)
    plays = models.IntegerField(default=0)
    revoked = models.BooleanField(default=False)
    device = models.ForeignKey("Device", on_delete=models.CASCADE, related_name="licenses")
    last_played_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        if self.revoked:
            return False
        now = timezone.now()
        return self.issued_at <= now <= self.expires_at

    class Meta:
        indexes = [
            models.Index(fields=["device", "package"]),
            models.Index(fields=["user", "expires_at"]),
        ]

    def is_active(self):
        if self.revoked:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def increment_play(self):
        self.plays = (self.plays or 0) + 1
        self.last_played_at = timezone.now()
        self.save(update_fields=["plays", "last_played_at"])

    def __str__(self):
        return self.id


class Device(models.Model):
    """
    Represents a client device (browser/PWA, desktop native, mobile).
    The device registers its public key (PEM) with the server so the server can
    wrap per-package DEKs to the device.
    """
    DEVICE_TYPES = [
        ("pwa", "Progressive Web App / Browser"),
        ("electron", "Electron / Tauri Desktop App"),
        ("windows_native", "Windows Native App"),
        ("android", "Android"),
        ("ios", "iOS"),
        ("react_native", "React Native"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=256, db_index=True)  # client-supplied id (GUID)
    name = models.CharField(max_length=200, blank=True)  # human-friendly name
    device_type = models.CharField(max_length=32, choices=DEVICE_TYPES, default="other")
    platform = models.CharField(max_length=128, blank=True, help_text="OS version / browser info")
    public_key_pem = models.TextField(help_text="Device public key (PEM) used to wrap DEKs")
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=True, help_text="Trusted device (admin/user flag)")
    revoked = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True, help_text="Optional client metadata")
    max_offline_items = models.PositiveIntegerField(null=True, blank=True, help_text="Max offline packages allowed on this device (optional)")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "device_id")
        indexes = [
            models.Index(fields=["user", "device_id"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.device_id} ({self.name})"

    def mark_seen(self):
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])


class Packaging(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "pending"),
        (STATUS_RUNNING, "running"),
        (STATUS_SUCCESS, "success"),
        (STATUS_FAILED, "failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey("podcasts.Episode", on_delete=models.CASCADE, related_name="packaging_jobs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    preset = models.CharField(max_length=64, default="medium")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    task_id = models.CharField(max_length=128, blank=True, null=True)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    callback_url = models.URLField(null=True, blank=True)
    webhook_secret = models.CharField(max_length=128, null=True, blank=True, help_text="HMAC secret used to sign webhook payloads")
    error = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["episode", "status"]),
            models.Index(fields=["user", "status"]),
        ]

    def mark_running(self, task_id=None):
        self.status = self.STATUS_RUNNING
        self.task_id = task_id or self.task_id
        self.started_at = timezone.now()
        self.save(update_fields=["status", "task_id", "started_at"])

    def mark_success(self, package):
        self.status = self.STATUS_SUCCESS
        self.package = package
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "package", "finished_at"])

    def mark_failed(self, error_text):
        self.status = self.STATUS_FAILED
        self.error = error_text[:4000]
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "error", "finished_at"])
