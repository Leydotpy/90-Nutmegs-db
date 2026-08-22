from .models import Feature

def create_exclusive(description=None):
    return Feature.objects.get_or_create(kind=Feature.Kind.EXCLUSIVE, description=description, is_content_featured=True)[0]


def create_early_access(early_access_hours: int, description=None):
    return Feature.objects.create(
        kind=Feature.Kind.EARLY_ACCESS,
        early_access_hours=early_access_hours,
        description=description,
        is_content_featured=True
    )

def create_for_transcription(description=None):
    return Feature.objects.get_or_create(kind=Feature.Kind.TRANSCRIPTION, description=description)[0]

def create_for_download(description=None):
    return Feature.objects.get_or_create(kind=Feature.Kind.DOWNLOADABLE, description=description)[0]

def create_for_vip_events(seats: int = None, description=None):
    return Feature.objects.create(
        kind=Feature.Kind.VIP_EVENTS,
        seats=seats,
        seats_limited=seats is not None,
        description=description
    )