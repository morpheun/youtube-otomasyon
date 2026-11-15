"""Claude ile Shorts hikaye senaryosu üretir (yapılandırılmış JSON)."""
import json
import random

import anthropic

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {"type": "string", "description": "Videonun ilk cümlesi (kanca). 1. sahnenin anlatımı TAM OLARAK bu cümleyle başlamalı."},
        "title_options": {
            "type": "array", "items": {"type": "string"},
            "description": "5 farklı başlık adayı. Her biri en fazla 40 karakter, sayı/saat/isim içersin, #shorts yazma.",
        },
        "thumb_text": {"type": "string", "description": "Videonun ilk 2 saniyesinde ekranda duracak 2-3 kelimelik yazı. Başlıktaki kelimeleri TEKRAR ETMESİN."},
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
    "required": ["hook", "title_options", "thumb_text", "description", "tags", "summary", "characters", "scenes"],
    "additionalProperties": False,
}

SYSTEM = """Sen viral YouTube Shorts için kısa animasyon hikayeleri yazan bir senaristsin.
Kurallar:
- KANCA (ilk cümle) videonun tamamıdır. İlk cümle: başlığın verdiği sözü doğrular, izleyicinin kapatamayacağı bir soru açar
  ve somut bir ayrıntı taşır (saat, sayı, isim, yer). En fazla 18 kelime. Önce 3 kanca düşün, en güçlüsünü "hook" alanına yaz;
  1. sahnenin anlatımı bu cümleyle başlasın. "Bir varmış bir yokmuş", "merhaba", "bugün size" ile BAŞLAMA.
- Kanal tanıtımı, "abone ol" çağrısı yok. Sona en fazla TEK bir çağrı koyabilirsin (ör. "Sence ne oldu? Yorumlara yaz.").
- Hikayenin net bir başı, gerilimi ve akılda kalan / ters köşe bir sonu olsun.
- Anlatım akıcı, sade, konuşma diline yakın olsun; seslendirmede doğal dursun.
- Şiddet, korku ve içerik aile dostu kalsın; telif hakkı olan karakterler, markalar, gerçek kişiler KULLANMA.
- Görsel tarifler İngilizce, anlatım istenen dilde olsun.
- Her image_prompt kendi başına anlaşılır olsun (karakterin adını değil görünüşünü yaz).
BAŞLIK VE KAPAK (title_options, thumb_text):
- Başlık ve kapak yazısı TEK bir paket: farklı kelimelerle aynı merakı versinler; kapak başlığı tekrar etmesin.
- Başlık en fazla 40 karakter (telefonda kesilmesin); sayı, saat ya da isim her sıfattan iyidir.
- En fazla 2 tamamen BÜYÜK HARFLİ kelime; "inanılmaz", "efsane", "şok" gibi şişirme kelimeler yok; en fazla 1 emoji.
- Kapak yazısı 2-3 kelime; hikayedeki en vurucu ifade ya da an (ör. "BENİ UNUTMA", "GECE 3'TE")."""


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
    from src.packaging import choose_title
    story["title"], story["title_score"], story["title_issues"] = choose_title(story["title_options"], story.get("thumb_text", ""))
    hook = story.get("hook", "").strip()
    if hook and story["scenes"] and not story["scenes"][0]["narration"].strip().startswith(hook[:20]):
        story["scenes"][0]["narration"] = f"{hook} {story['scenes'][0]['narration']}".strip()
    story["theme"] = theme
    story["art_style"] = random.choice(cfg["art_styles"])
    if not story["scenes"]:
        raise RuntimeError("Senaryoda sahne yok.")
    return story
