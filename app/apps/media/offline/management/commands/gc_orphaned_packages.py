from datetime import timedelta

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.media.offline.models import Package


class Command(BaseCommand):
    help = "Delete offline packages with no active licenses older than X days"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Age threshold in days")

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        # orphan = no licenses or only expired/revoked licenses
        packages = Package.objects.filter(created_at__lt=cutoff)
        removed = 0
        for p in packages:
            active_licenses = p.licenses.filter(revoked=False, expires_at__gt=timezone.now()).exists()
            if not active_licenses:
                try:
                    # delete storage object if exists
                    if p.storage_key and default_storage.exists(p.storage_key):
                        default_storage.delete(p.storage_key)
                except Exception:
                    pass
                p.delete()
                removed += 1
        self.stdout.write(self.style.SUCCESS(f"Removed {removed} orphan packages older than {cutoff.date()}"))
