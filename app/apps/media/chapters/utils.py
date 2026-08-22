from collections import defaultdict

CHAPTER_INTERVAL = 300  # 5 minutes

def build_chapters(segments: list[dict]) -> list[dict]:
    buckets = defaultdict(list)

    for seg in segments:
        bucket = int(seg["start_time"] // CHAPTER_INTERVAL)
        buckets[bucket].append(seg["word"])

    chapters = []
    for bucket, words in buckets.items():
        text = " ".join(words)
        chapters.append({
            "start_time": bucket * CHAPTER_INTERVAL,
            "title": summarize(text),
        })
    return chapters


def summarize(text: str) -> str:
    from openai import OpenAI
    client = OpenAI()

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=f"Give a short podcast chapter title:\n{text[:1500]}"
    )
    return resp.output_text.strip()

