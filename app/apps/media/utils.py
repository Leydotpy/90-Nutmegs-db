import mimetypes
import os

import ffmpeg
from PIL import Image
from django.db.models.fields.files import FieldFile

from apps.thumbnail.models import Thumbnail
from apps.thumbnail.utils import ThumbnailGenerator

AUDIO_PRESETS = {
    "low": {"bitrate": "64k", "kbps": 64, "sample_rate": 22050},
    "medium": {"bitrate": "128k", "kbps": 128, "sample_rate": 44100},
    "high": {"bitrate": "192k", "kbps": 192, "sample_rate": 44100},
}


def probe(path: str) -> dict:
    """Return ffprobe information for an input file."""
    return ffmpeg.probe(path)


def get_audio_duration_seconds(path: str) -> float:
    info = probe(path)
    stream = next(s for s in info["streams"] if s["codec_type"] == "audio")
    return float(stream["duration"])


def detect_master_audio_info(path: str) -> dict:
    info = probe(path)
    # find audio stream
    audio_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not audio_streams:
        raise ValueError("No audio stream detected")
    a = audio_streams[0]
    bitrate = int(a.get("bit_rate") or info.get("format", {}).get("bit_rate") or 0) // 1000
    sample_rate = int(a.get("sample_rate") or 44100)
    codec = a.get("codec_name")
    duration = float(info.get("format", {}).get("duration") or 0)
    title = info.get("format", {}).get("tags", {}).get("title", "") or ""
    return {"bitrate_kbps": bitrate, "sample_rate": sample_rate, "codec": codec, "duration": duration, "title": title}


def transcode_to_variant(master_path: str, out_path: str, preset: dict):
    """
    Create a single variant (mp3/aac) using ffmpeg-python.
    preset: {"bitrate": "128k", "kbps":128, "sample_rate":44100}
    """
    # ensure output dir exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Build ffmpeg pipeline
    stream = ffmpeg.input(master_path)
    audio = (
        ffmpeg
        .output(stream.audio, out_path,
                **{
                    "acodec": "libmp3lame",
                    "ab": preset["bitrate"],
                    "ar": str(preset["sample_rate"]),
                    "ac": 2,
                })
    )
    # run with reasonable timeouts and overwrite
    ffmpeg.run(audio, overwrite_output=True)


def create_hls_audio(master_path: str, out_dir: str, preset: dict, segment_time=10):
    """
    Generate HLS (audio-only) playlist + segments locally under out_dir.
    Returns path to master m3u8.
    """
    os.makedirs(out_dir, exist_ok=True)
    playlist_path = os.path.join(out_dir, "index.m3u8")
    segment_pattern = os.path.join(out_dir, "seg_%03d.ts")

    (
        ffmpeg
        .input(master_path)
        .output(playlist_path,
                format='hls',
                hls_time=segment_time,
                hls_list_size=0,  # keep all
                hls_segment_filename=segment_pattern,
                acodec='aac',
                ar=str(preset['sample_rate']),
                ab=preset['bitrate'],
                ac=2)
        .run(overwrite_output=True)
    )
    return playlist_path


def get_file_metadata(file: FieldFile) -> dict:
    try:
        return ffmpeg.probe(file.path)
    except ffmpeg.Error as e:
        print(str(e))
        raise e


def get_file_type(instance):
    file = instance.get_media_file()
    name, ext = os.path.splitext(file)
    mime_type, _ = mimetypes.guess_type(file)
    return ext, mime_type


def is_video(file: FieldFile):
    return mimetypes.guess_type(file.url)[0].startswith("video")


def generate_image_thumbnail(self):
    if not Thumbnail.objects.exist(self):
        ThumbnailGenerator.generate_thumbnail(self, self.pk)
