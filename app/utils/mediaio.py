import os
import shutil
import tempfile
import subprocess
import ffmpeg
from typing import Optional, Generator
from contextlib import contextmanager
from django.conf import settings

PODCAST_PROMOTIONS_FOLDER = getattr(settings, 'PODCAST_PROMOTIONS_FOLDER')

def video_to_gif(
        video_path: str,
        gif_path: str,
        *,
        fps: int = 10,
        width: int = 640,
        start_time: Optional[int] = None,
        duration: Optional[int] = None,
        loop: int = 0,
        optimize_with_gifsicle: bool = True,
        gifsicle_opts: Optional[list] = None,
):
    palette_path = "palette_temp.png"

    def make_input(path):
        kwargs = {}
        if start_time is not None:
            kwargs["ss"] = start_time
        if duration is not None:
            kwargs["t"] = duration
        return ffmpeg.input(path, **kwargs)

    try:

        # Generate palette
        video_for_palette = make_input(video_path)
        (
            video_for_palette
            .filter("fps", fps)
            .filter("scale", width, -1, flags="lanczos")
            .filter("palettegen")
            .output(palette_path)
            .overwrite_output()
            .run(quiet=True)
        )

        # Use palette to generate GIF
        video_for_gif = make_input(video_path)
        palette_input = ffmpeg.input(palette_path)
        filter_complex = f"[0:v]fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse"

        (
            ffmpeg
            .output(
                video_for_gif,
                palette_input,
                gif_path,
                filter_complex=filter_complex,

            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Optimize with gifsicle if requested
        if optimize_with_gifsicle:
            default_opts = ["-O3", "--colors", "256", "--loopcount", str(loop)]
            gifsicle_cmd = ["gifsicle"] + (gifsicle_opts or default_opts) + [gif_path, "-o", gif_path]
            try:
                subprocess.run(gifsicle_cmd, check=True)
            except FileNotFoundError:
                print("gifsicle not installed; skipping optimization")
            except subprocess.CalledProcessError:
                print("gifsicle optimization failed; leaving GIF as-is")

        print(f"GIF saved at: {gif_path}")
        return gif_path

    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
    finally:
        if os.path.exists(palette_path):
            os.remove(palette_path)

@contextmanager
def pluck(django_file, *, ffprobe_exe: Optional[str] = None) -> Generator[dict, None, None]:
    """
    Context manager that yields ffmpeg.probe(info) for a Django FileField-like object.
    If the file is not available on disk (no .path or path doesn't exist), it writes
    the file to a temporary file and cleans it up on exit.

    Args:
        django_file: File-like object (e.g., Django FieldFile / InMemoryUploadedFile).
        ffprobe_exe: Optional full path to ffprobe executable. If provided, its directory
                     is prepended to PATH so ffmpeg-python can find it.

    Yields:
        dict: result of ffmpeg.probe(target)
    Raises:
        RuntimeError: if ffprobe cannot be found.
    """
    # Determine whether the file already exists on disk
    candidate_path = getattr(django_file, "path", None) or ""
    if candidate_path and os.path.exists(candidate_path):
        target = candidate_path
        cleanup = False
    else:
        # Ensure we're at start of file (if it supports seek)
        try:
            django_file.seek(0)
        except Exception:
            pass

        suffix = os.path.splitext(getattr(django_file, "name", "") or "")[1] or ""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            data = django_file.read()
            if isinstance(data, str):
                data = data.encode()
            tmp.write(data)
            tmp.flush()
            tmp.close()  # close so ffprobe/ffmpeg can open it on Windows
            target = tmp.name
            cleanup = True
        except Exception:
            # cleanup partial temp file on error
            try:
                tmp.close()
            except Exception:
                pass
            try:
                os.remove(tmp.name)
            except Exception:
                pass
            raise

    # If user supplied ffprobe_exe, ensure its directory is on PATH
    if ffprobe_exe:
        if not os.path.isfile(ffprobe_exe):
            # if it's not a file, treat it as not found
            raise RuntimeError(f"ffprobe_exe path not found: {ffprobe_exe}")
        ffprobe_dir = os.path.dirname(os.path.abspath(ffprobe_exe))
        os.environ["PATH"] = ffprobe_dir + os.pathsep + os.environ.get("PATH", "")

    # Verify ffprobe is available
    if not shutil.which("ffprobe"):
        # cleanup before raising if we created a temp file
        if cleanup and os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass
        raise RuntimeError("ffprobe not found on PATH. Install ffmpeg or provide ffprobe_exe.")

    try:
        info = ffmpeg.probe(target)
        yield info
    finally:
        if cleanup:
            try:
                os.remove(target)
            except Exception:
                pass
