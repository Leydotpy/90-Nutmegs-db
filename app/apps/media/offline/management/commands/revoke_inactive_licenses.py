# apps/media/management/commands/revoke_inactive_devices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.media.offline.models import Device

class Command(BaseCommand):
    help = "Revoke devices that have not been seen for X days"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Days of inactivity before revoking")

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = Device.objects.filter(last_seen_at__lt=cutoff, revoked=False)
        count = qs.update(revoked=True)
        self.stdout.write(self.style.SUCCESS(f"Revoked {count} devices not seen since {cutoff.isoformat()}"))
