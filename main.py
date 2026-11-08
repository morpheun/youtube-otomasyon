"""Otomatik hikaye animasyonu Shorts üretip YouTube'a yükler.

Kullanım:
  python main.py                 # üret + yükle
  python main.py --no-upload     # sadece üret (output/ klasörüne)
  python main.py --story story.json --no-upload   # hazır senaryodan üret
"""
import argparse
import datetime as dt
import json
import os
import random
import shutil

from src import images, render, story as story_mod, tts

ROOT = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(ROOT, "data", "history.json")


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--story", help="Claude yerine bu JSON senaryoyu kullan")
    ap.add_argument("--keep-work", action="store_true", help="ara dosyaları silme")
    args = ap.parse_args()

    cfg = load_json(os.path.join(ROOT, "config.json"), {})
    history = load_json(HISTORY, [])

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(ROOT, "output")
    work = os.path.join(out_dir, f"work-{stamp}")
    os.makedirs(work, exist_ok=True)

    # 1) Senaryo
    if args.story:
        story = load_json(args.story, None)
        story.setdefault("art_style", random.choice(cfg["art_styles"]))
    else:
        print("1/4 Senaryo yazılıyor (Claude)...")
        story = story_mod.generate_story(cfg, history)
    print(f"   Başlık: {story['title']}  ({len(story['scenes'])} sahne)")
    with open(os.path.join(out_dir, f"{stamp}.json"), "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)

    # 2) Seslendirme + 3) Görseller
    seed = random.randint(1, 10_000_000)
    scenes = []
    for i, sc in enumerate(story["scenes"]):
        print(f"2-3/4 Sahne {i + 1}/{len(story['scenes'])}: ses + görsel")
        a = tts.synthesize(sc["narration"], cfg["tts_voice"], cfg["tts_rate"], os.path.join(work, f"tts_{i:02d}.mp3"))
        img = sc.get("image_path") or images.generate_image(
            images.build_prompt(story, sc), os.path.join(work, f"img_{i:02d}.jpg"), cfg, seed + i * 7)
        scenes.append({"image": img, "audio": a["path"], "duration": a["duration"], "words": a["words"]})

    # 4) Montaj
    print("4/4 Video birleştiriliyor (ffmpeg)...")
    video = os.path.join(out_dir, f"{stamp}.mp4")
    total = render.render(scenes, work, video, cfg, os.path.join(ROOT, "assets", "music"))
    print(f"   Hazır: {video}  ({total:.1f} sn)")
    if total > 180:
        raise RuntimeError("Video 3 dakikadan uzun; Shorts sayılmaz.")

    # Yükleme
    video_id = None
    if not args.no_upload:
        from src.upload import upload_video
        title = story["title"].strip()
        if "#shorts" not in title.lower():
            title = f"{title} #shorts"
        desc = f"{story['description']}\n\n#shorts #hikaye #animasyon"
        tags = list(dict.fromkeys(story.get("tags", []) + cfg["default_tags"]))
        print("YouTube'a yükleniyor...")
        video_id = upload_video(video, title, desc, tags, cfg)
        print(f"   Yüklendi: https://youtube.com/shorts/{video_id}")

    history.append({
        "date": stamp, "title": story["title"], "summary": story.get("summary", story["title"]),
        "theme": story.get("theme"), "video_id": video_id,
    })
    if not args.no_upload or not args.story:
        os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)

    # GitHub Actions özetine yaz
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### {story['title']}\n\nSüre: {total:.1f} sn\n\n")
            if video_id:
                f.write(f"https://youtube.com/shorts/{video_id}\n")


if __name__ == "__main__":
    main()
