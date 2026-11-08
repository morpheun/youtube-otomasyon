"""Görselleri, sesi ve altyazıyı ffmpeg ile dikey Shorts videosuna dönüştürür."""
import glob
import os
import random
import subprocess

GAP = 0.35        # sahneler arası nefes payı (sn)
TAIL = 0.9        # son sahneden sonra bekleme (sn)
FADE_FRAMES = 6


def _run(cmd: list[str], cwd: str | None = None) -> None:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg hatası:\n{' '.join(cmd)}\n{p.stderr[-3000:]}")


def _motion(kind: str, n: int) -> str:
    """Ken Burns hareketleri: yakınlaş / uzaklaş / yatay kaydır / dikey kaydır."""
    c = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return {
        "zoom_in": f"z='1+0.15*on/{n}':{c}",
        "zoom_out": f"z='1.15-0.15*on/{n}':{c}",
        "pan_right": f"z=1.15:x='(iw-iw/zoom)*on/{n}':y='ih/2-(ih/zoom/2)'",
        "pan_left": f"z=1.15:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'",
        "pan_up": f"z=1.15:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/{n})'",
    }[kind]


def scene_clip(image: str, frames: int, out: str, cfg: dict, kind: str) -> None:
    w, h, fps = cfg["width"], cfg["height"], cfg["fps"]
    vf = (
        f"scale={w * 2}:{h * 2}:flags=lanczos,"
        f"zoompan={_motion(kind, frames)}:d={frames}:s={w}x{h}:fps={fps},"
        f"fade=t=in:s=0:n={FADE_FRAMES},fade=t=out:s={frames - FADE_FRAMES}:n={FADE_FRAMES},"
        "format=yuv420p"
    )
    _run(["ffmpeg", "-y", "-i", image, "-vf", vf, "-frames:v", str(frames),
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", str(fps), out])


def padded_audio(src: str, seconds: float, out: str) -> None:
    _run(["ffmpeg", "-y", "-i", src, "-af", "apad", "-t", f"{seconds:.3f}",
          "-ar", "44100", "-ac", "2", out])


def _ass_time(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def tr_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def write_ass(scene_words: list[list[dict]], path: str, cfg: dict) -> None:
    """Kelime gruplarını büyük, ortalı, kontur çizgili altyazı olarak yazar; o an okunan kelime sarı.
    Gruplar sahne sınırını aşmaz."""
    n = cfg["subtitle_words_per_line"]
    groups = [ws[i:i + n] for ws in scene_words for i in range(0, len(ws), n)]
    lines = []
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else g[-1]["end"] + 0.3
        g_end = min(g_end, g[-1]["end"] + 0.6)
        for wi, wd in enumerate(g):
            start = wd["start"]
            end = g[wi + 1]["start"] if wi + 1 < len(g) else g_end
            parts = []
            for k, x in enumerate(g):
                t = tr_upper(x["text"]).replace("{", "(").replace("}", ")")
                parts.append(r"{\c&H00E5FF&}" + t + r"{\c&HFFFFFF&}" if k == wi else t)
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Sub,,0,0,0,,{' '.join(parts)}")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {cfg['width']}
PlayResY: {cfg['height']}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{cfg['subtitle_font']},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")


def render(scenes: list[dict], workdir: str, out_path: str, cfg: dict, music_dir: str) -> float:
    """scenes: [{image, audio, duration, words}] -> out_path. Toplam süreyi döndürür."""
    fps = cfg["fps"]
    kinds = ["zoom_in", "pan_right", "zoom_out", "pan_up", "pan_left"]
    random.shuffle(kinds)

    clip_list, audio_list, scene_words = [], [], []
    t0 = 0.0
    for i, s in enumerate(scenes):
        target = s["duration"] + (TAIL if i == len(scenes) - 1 else GAP)
        frames = max(int(round(target * fps)), FADE_FRAMES * 2 + 1)
        seconds = frames / fps  # görüntü ve ses birebir aynı uzunlukta olsun

        clip = os.path.join(workdir, f"clip_{i:02d}.mp4")
        scene_clip(s["image"], frames, clip, cfg, kinds[i % len(kinds)])
        wav = os.path.join(workdir, f"voice_{i:02d}.wav")
        padded_audio(s["audio"], seconds, wav)

        clip_list.append(os.path.basename(clip))
        audio_list.append(os.path.basename(wav))
        scene_words.append([{"text": w["text"], "start": w["start"] + t0, "end": w["end"] + t0} for w in s["words"]])
        t0 += seconds

    with open(os.path.join(workdir, "clips.txt"), "w") as f:
        f.writelines(f"file '{c}'\n" for c in clip_list)
    with open(os.path.join(workdir, "voices.txt"), "w") as f:
        f.writelines(f"file '{a}'\n" for a in audio_list)
    write_ass(scene_words, os.path.join(workdir, "subs.ass"), cfg)

    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))
    sub_filter = f"subtitles=subs.ass:fontsdir='{fonts_dir}'" if os.path.isdir(fonts_dir) else "subtitles=subs.ass"

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clips.txt",
           "-f", "concat", "-safe", "0", "-i", "voices.txt"]
    music = sorted(glob.glob(os.path.join(music_dir, "*.mp3")) + glob.glob(os.path.join(music_dir, "*.m4a")))
    if music:
        cmd += ["-stream_loop", "-1", "-i", os.path.abspath(random.choice(music))]
        afilter = (f"[2:a]volume={cfg['music_volume']},afade=t=out:st={max(t0 - 1.5, 0):.2f}:d=1.5[m];"
                   "[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]")
    else:
        afilter = "[1:a]loudnorm=I=-14:TP=-1.5[a]"

    cmd += ["-filter_complex", f"[0:v]{sub_filter}[v];{afilter}",
            "-map", "[v]", "-map", "[a]", "-t", f"{t0:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart",
            os.path.abspath(out_path)]
    _run(cmd, cwd=workdir)
    return t0
