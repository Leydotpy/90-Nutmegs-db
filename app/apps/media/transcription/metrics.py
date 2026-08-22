from prometheus_client import Counter, Histogram

# Total successful transcriptions
TRANSCRIPTIONS_TOTAL = Counter(
    "podcast_transcriptions_total",
    "Total number of completed transcriptions",
    ["provider"]
)

# Failed transcriptions
TRANSCRIPTIONS_FAILED = Counter(
    "podcast_transcriptions_failed_total",
    "Total number of failed transcriptions",
    ["provider", "reason"]
)

# End-to-end transcription duration
TRANSCRIPTION_DURATION = Histogram(
    "podcast_transcription_duration_seconds",
    "Time taken to transcribe an episode",
    ["provider"],
    buckets=(10, 30, 60, 120, 300, 600, 900, 1200)
)

# Audio length vs processing time (optional but very useful)
AUDIO_DURATION_SECONDS = Histogram(
    "podcast_audio_duration_seconds",
    "Duration of audio sent for transcription",
    buckets=(60, 300, 600, 1200, 1800, 3600)
)


