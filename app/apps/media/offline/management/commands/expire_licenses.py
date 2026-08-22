from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.media.offline.models import License


class Command(BaseCommand):
    help = "Expire offline licenses whose expires_at < now"

    def handle(self, *args, **options):
        now = timezone.now()
        qs = License.objects.filter(expires_at__lt=now, revoked=False)
        count = qs.update(revoked=True)
        self.stdout.write(self.style.SUCCESS(f"Marked {count} licenses revoked (expired)"))
