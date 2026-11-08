"""Sahne görsellerini üretir (Pollinations / FLUX)."""
import os
import random
import time
import urllib.parse

import requests
from PIL import Image

NEGATIVE = "no text, no letters, no watermark, no logo, no subtitles"


def _pollinations(prompt: str, w: int, h: int, seed: int, model: str) -> bytes:
    q = urllib.parse.quote(prompt, safe="")
    params = {"width": w, "height": h, "seed": seed, "model": model, "nologo": "true", "enhance": "false"}
    key = os.environ.get("POLLINATIONS_API_KEY")
    if key:
        url = f"https://gen.pollinations.ai/image/{q}"
        headers = {"Authorization": f"Bearer {key}"}
    else:  # anahtarsız eski uç nokta (yavaş, sınırlı)
        url = f"https://image.pollinations.ai/prompt/{q}"
        headers = {}
    r = requests.get(url, params=params, headers=headers, timeout=180)
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(f"Görsel yerine {r.headers.get('content-type')} döndü: {r.text[:200]}")
    return r.content


def generate_image(prompt: str, out_path: str, cfg: dict, seed: int, retries: int = 4) -> str:
    w, h = cfg["width"], cfg["height"]
    last = None
    for attempt in range(retries):
        try:
            data = _pollinations(prompt, w, h, seed + attempt, cfg.get("pollinations_model", "flux"))
            tmp = out_path + ".raw"
            with open(tmp, "wb") as f:
                f.write(data)
            _fit(tmp, out_path, w, h)
            os.remove(tmp)
            return out_path
        except Exception as e:
            last = e
            time.sleep(8 * (attempt + 1) + random.random() * 3)
    raise RuntimeError(f"Görsel üretilemedi: {last}")


def _fit(src: str, dst: str, w: int, h: int) -> None:
    """Görseli kırparak tam w x h dikey kareye oturtur."""
    im = Image.open(src).convert("RGB")
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - w) // 2, (im.height - h) // 2
    im.crop((left, top, left + w, top + h)).save(dst, quality=95)


def build_prompt(story: dict, scene: dict) -> str:
    return f"{story['art_style']}. {scene['image_prompt']}. Characters: {story['characters']}. Vertical 9:16 composition, {NEGATIVE}"
