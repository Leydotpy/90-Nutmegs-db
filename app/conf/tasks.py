"""Fixed scheduler entry points; never accept an arbitrary management command."""

from celery import shared_task
from django.core.management import call_command


@shared_task
def expire_offline_licenses() -> None:
    call_command("expire_licenses")


@shared_task
def revoke_inactive_devices() -> None:
    call_command("revoke_inactive_licenses", days=90)


@shared_task
def collect_orphaned_packages() -> None:
    call_command("gc_orphaned_packages", days=30)
