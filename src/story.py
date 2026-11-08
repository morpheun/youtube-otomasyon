"""Claude ile Shorts hikaye senaryosu üretir (yapılandırılmış JSON)."""
import json
import random

import anthropic

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "YouTube başlığı, merak uyandıran, en fazla 80 karakter, emoji olabilir"},
        "description": {"type": "string", "description": "2-3 cümlelik YouTube açıklaması + hashtagler"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string", "description": "Hikayenin tek cümlelik özeti (tekrarı önlemek için kaydedilir)"},
        "characters": {
            "type": "string",
            "description": "ENGLISH. Ana karakterlerin her sahnede aynı kalacak çok net görsel tarifi (yaş, kıyafet, renkler, tür).",
        },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "Bu sahnede seslendirilecek Türkçe anlatım (1-2 kısa cümle)"},
                    "image_prompt": {
                        "type": "string",
                        "description": "ENGLISH. Sahnenin görsel tarifi: kim, ne yapıyor, nerede, kamera açısı, ışık. Metin/yazı içermesin.",
                    },
                },
                "required": ["narration", "image_prompt"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "tags", "summary", "characters", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """Sen viral YouTube Shorts için kısa animasyon hikayeleri yazan bir senaristsin.
Kurallar:
- İlk cümle izleyiciyi ilk 2 saniyede yakalayan güçlü bir kanca olmalı (soru, şok edici durum veya gizem).
- Hikayenin net bir başı, gerilimi ve akılda kalan / ters köşe bir sonu olsun.
- Anlatım akıcı, sade, konuşma diline yakın olsun; seslendirmede doğal dursun.
- Şiddet, korku ve içerik aile dostu kalsın; telif hakkı olan karakterler, markalar, gerçek kişiler KULLANMA.
- Görsel tarifler İngilizce, anlatım istenen dilde olsun.
- Her image_prompt kendi başına anlaşılır olsun (karakterin adını değil görünüşünü yaz)."""


def generate_story(cfg: dict, history: list[dict]) -> dict:
    client = anthropic.Anthropic()

    theme = random.choice(cfg["story_themes"])
    recent = "\n".join(f"- {h['summary']}" for h in history[-60:]) or "(henüz yok)"
    words = int(cfg["target_seconds"] * 2.4)  # ~2.4 kelime/sn Türkçe anlatım

    prompt = f"""Dil: {cfg['language']}
Tür: {cfg['genre']}
Bu videonun teması: {theme}
Sahne sayısı: tam olarak {cfg['scene_count']}
Toplam anlatım uzunluğu: yaklaşık {words} kelime (≈{cfg['target_seconds']} saniye).

Daha önce anlatılan hikayeler (bunlara BENZEMEYEN yepyeni bir hikaye yaz):
{recent}

Başlığın sonuna #shorts ekleme, onu sistem ekleyecek."""

    response = client.beta.messages.create(
        model=cfg["claude_model"],
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": STORY_SCHEMA},
        },
        # Güvenlik filtresi bir isteği reddederse sunucu tarafında otomatik yedek modele geçer.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude isteği reddetti: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Senaryo yanıtı max_tokens sınırına takıldı.")

    text = next(b.text for b in response.content if b.type == "text")
    story = json.loads(text)
    story["theme"] = theme
    story["art_style"] = random.choice(cfg["art_styles"])
    if not story["scenes"]:
        raise RuntimeError("Senaryoda sahne yok.")
    return story
