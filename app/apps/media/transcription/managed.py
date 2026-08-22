import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import ffmpeg
from django.conf import settings

OPENAI_API_KEY = getattr(settings, "OPENAI_API_KEY", None)

# Optional imports for providers — import lazily in functions
# from openai import OpenAI  # used only if provider == 'openai'
# from google.cloud import speech_v1 as speech, storage  # used only for provider == 'google'

logger = logging.getLogger(__name__)


# Helper: convert master audio to WAV (mono 16k), returns path to wav
def convert_to_wav_16k_mono(input_path: str, out_dir: str) -> str:
    out_path = os.path.join(out_dir, "master_for_asr.wav")
    # ffmpeg-python pipeline: force mono, 16k sample rate, PCM S16LE WAV
    (
        ffmpeg
        .input(input_path)
        .output(out_path, ac=1, ar="16000", format="wav", acodec="pcm_s16le")
        .overwrite_output()
        .run(quiet=True)
    )
    return out_path


# OpenAI transcription helper
def transcribe_with_openai(wav_path: str, model: str = "gpt-4o-transcribe", extra: Optional[Dict[str, Any]] = None) -> \
        Dict[str, Any]:
    """
    Uses OpenAI audio.transcriptions.create (file upload).
    Requires OPENAI_API_KEY in env and `openai` Python package (new client).
    Returns dict with keys: text, segments (if available), language
    """
    # lazy import
    from openai import OpenAI
    client = OpenAI(api_key="OPENAI_API_KEY")
    # open file in binary
    with open(wav_path, "rb") as audio_file:
        # docs show client.audio.transcriptions.create(...) usage.
        params = {
            "file": audio_file,
            "model": model,
            # optionally: "response_format": "verbose_json"
        }
        if extra:
            params.update(extra)
        # The returned object often has .text or .get("text")
        resp = client.audio.transcriptions.create(**params)
    # Normalise possible return shapes
    text = getattr(resp, "text", None) or resp.get("text") if isinstance(resp, dict) else None
    # Some models can return segments if response_format includes timestamps
    segments = resp.get("segments") if isinstance(resp, dict) else None
    language = resp.get("language") if isinstance(resp, dict) else None
    return {"text": text, "segments": segments, "language": language}


# Google Cloud transcription helper (GCS-based long-running recognize)
def transcribe_with_google_gcs(wav_path: str, gcs_bucket: str, gcs_prefix: str, language_code: str = "en-US",
                               sample_rate_hertz: int = 16000, encoding: str = "LINEAR16",
                               speech_contexts: Optional[list] = None) -> Dict[str, Any]:
    """
    Uploads wav to GCS, calls long_running_recognize, waits for result, then deletes GCS object.
    Requires GOOGLE_APPLICATION_CREDENTIALS env pointing to service account JSON.
    Returns dict with text, segments, language.
    """
    from google.cloud import storage, speech_v1 as speech

    # Upload to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket)
    key = f"{gcs_prefix.rstrip('/')}/{Path(wav_path).name}"
    blob = bucket.blob(key)
    blob.upload_from_filename(wav_path, content_type="audio/wav")
    gcs_uri = f"gs://{gcs_bucket}/{key}"

    speech_client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
        language_code=language_code,
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,  # if you want word-level timestamps
    )
    audio = speech.RecognitionAudio(uri=gcs_uri)

    operation = speech_client.long_running_recognize(config=config, audio=audio)
    logger.info("Google STT operation started: %s", operation.operation.name)

    # Wait for operation to finish (timeout controlled by operation.result(timeout=...))
    response = operation.result(timeout=600)  # adjust timeout if you need longer jobs

    # Collate transcripts
    texts = []
    segments = []
    for result in response.results:
        # result.alternatives is a list; take the first
        alt = result.alternatives[0]
        texts.append(alt.transcript)
        # if word offsets present, you can build segments
        if alt.words:
            for w in alt.words:
                segments.append({
                    "word": w.word,
                    "start_time": w.start_time.total_seconds(),
                    "end_time": w.end_time.total_seconds()
                })

    # cleanup: delete blob
    try:
        blob.delete()
    except Exception as exc:
        logger.warning("Failed to delete temporary GCS object %s: %s", gcs_uri, exc)

    full_text = "\n".join(texts)
    return {"text": full_text, "segments": segments, "language": language_code}
