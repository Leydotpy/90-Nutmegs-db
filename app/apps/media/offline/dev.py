import os
import shutil
import tempfile
import uuid

from django.core.files import File as DjangoFile
from django.core.files.storage import default_storage

from apps.media.audio.models import Audio
from apps.media.offline.models import Package


def create_package_direct_storage(episode, master_audio: Audio):
    storage = default_storage
    storage_key = f"offline/pkg/{episode.id}/{uuid.uuid4().hex}.pkg"

    # open a write handle and stream into it (FileSystemStorage supports this)
    with storage.open(storage_key, "wb") as dest:
        for chunk in master_audio.file.chunks():
            # optionally process chunk (encrypt) before writing
            dest.write(chunk)

    # now create the model and point FileField to the stored key
    pkg = Package.objects.create(episode=episode, file=storage_key)
    return pkg


def build_package_to_disk(master_file_path, out_pkg_path):
    """
    Example packaging function:
    - reads master_file_path in chunks,
    - writes a simple container to out_pkg_path.
    Replace with your streaming encryption or ffmpeg pipeline.
    """
    with open(master_file_path, "rb") as inp, open(out_pkg_path, "wb") as out:
        while True:
            chunk = inp.read(64 * 1024)
            if not chunk:
                break
            # do any processing/encryption here; this example copies it
            out.write(chunk)


def create_offline_package_development(episode, master_audio: Audio):
    """
    1. Download master locally if needed (Audio.file may be on storage).
    2. Build package to a temp file on disk (streaming).
    3. Save package into OfflinePackage.package_file via FileField.save().
    4. Optionally delete the tmp file.
    """
    tmpdir = tempfile.mkdtemp(prefix=f"offline-{episode.id}-")
    try:
        # 1) get local path for master (download from storage to local temp)
        master_local = os.path.join(tmpdir, "master.bin")
        with open(master_local, "wb") as fh:
            for chunk in master_audio.file.chunks():
                fh.write(chunk)

        # 2) build package streaming to a file
        out_pkg = os.path.join(tmpdir, "package.pkg")
        build_package_to_disk(master_local, out_pkg)

        # 3) save to model FileField using DjangoFile - this uses DEFAULT_FILE_STORAGE
        pkg = Package.objects.create(episode=episode)
        with open(out_pkg, "rb") as f:
            django_file = DjangoFile(f, name=os.path.basename(out_pkg))
            # You can control the final storage path by passing a full name:
            # pkg.package_file.save(f"offline/packages/{episode.id}/{os.path.basename(out_pkg)}", django_file, save=True)
            pkg.file.save(django_file.name, django_file, save=True)

        # pkg.package_file.name now contains the storage key (relative path)
        return pkg
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
