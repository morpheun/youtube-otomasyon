"""edge-tts ile sahne sahne seslendirme + kelime zamanlamaları."""
import asyncio
import subprocess

import edge_tts


def audio_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


async def _synth(text: str, voice: str, rate: str, out_path: str) -> list[dict]:
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # offset/duration 100 nanosaniye biriminde
                start = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": start, "end": start + chunk["duration"] / 1e7})
    return words


def synthesize(text: str, voice: str, rate: str, out_path: str, retries: int = 3) -> dict:
    last = None
    for attempt in range(retries):
        try:
            words = asyncio.run(_synth(text, voice, rate, out_path))
            dur = audio_duration(out_path)
            if not words:  # zamanlama gelmezse kelimeleri eşit dağıt
                toks = text.split()
                step = dur / max(len(toks), 1)
                words = [{"text": t, "start": i * step, "end": (i + 1) * step} for i, t in enumerate(toks)]
            return {"path": out_path, "duration": dur, "words": words}
        except Exception as e:  # ağ hataları vb.
            last = e
    raise RuntimeError(f"Seslendirme başarısız: {last}")
