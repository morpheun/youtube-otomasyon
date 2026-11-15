"""Başlık + kapak yazısı denetimi (yt-package kuralları, Türkçe uyumlu).

Kurallar (.claude/skills/yt-package):
- 40 karakter telefon akışında, 60 karakter masaüstü aramada kesilir.
- Sayı, saat ya da tarih her sıfattan iyidir.
- En fazla 2 tamamen büyük harfli kelime; fazlası spam gibi okunur.
- Kapak yazısı en fazla 3 kelime ve başlıktaki kelimeleri tekrar etmez.
"""
import re

BANNED = {"inanılmaz", "efsane", "şok", "şoke", "olay", "çılgın"}
_WORD = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû']+")


def _lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def words(s: str) -> list[str]:
    return _WORD.findall(s)


def _stem(w: str) -> str:
    """Türkçe ekleri kabaca atar: 'kuyudan' ve 'kuyuya' aynı kök sayılsın."""
    w = _lower(w).strip("'")
    return w[:5] if len(w) > 5 else w


def lint_title(title: str, thumb: str = "") -> tuple[int, list[str]]:
    """(puan 0-100, sorunlar) döndürür."""
    t = title.strip()
    score, issues = 100, []
    n = len(t)
    if n > 60:
        score -= 30; issues.append(f"{n} karakter: masaüstü aramada kesilir (60)")
    elif n > 40:
        score -= 6; issues.append(f"{n} karakter: telefonda kesilebilir (40)")
    if not re.search(r"\d", t):
        score -= 10; issues.append("sayı, saat ya da tarih yok")
    caps = [w for w in words(t) if len(w) > 1 and w.isupper() and not w.isdigit()]
    if len(caps) > 2:
        score -= 15; issues.append(f"{len(caps)} büyük harfli kelime (en fazla 2)")
    if any(_lower(w) in BANNED for w in words(t)):
        score -= 10; issues.append("şişirilmiş kelime (inanılmaz/efsane/şok...)")
    emoji = len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", t))
    if emoji > 1:
        score -= 5; issues.append("birden fazla emoji")
    if thumb:
        tw = words(thumb)
        if len(tw) > 3:
            score -= 10; issues.append(f"kapak yazısı {len(tw)} kelime (en fazla 3)")
        common = {_stem(w) for w in tw} & {_stem(w) for w in words(t)}
        if common:
            score -= 20; issues.append("kapak yazısı başlıktaki kelimeyi tekrar ediyor: " + ", ".join(sorted(common)))
    return max(0, score), issues


def choose_title(options: list[str], thumb: str = "") -> tuple[str, int, list[str]]:
    """En yüksek puanlı başlığı seçer (eşitlikte ilk sıradaki)."""
    best = None
    for o in options:
        o = o.strip().replace("#shorts", "").replace("#Shorts", "").strip()
        if not o:
            continue
        s, iss = lint_title(o, thumb)
        if best is None or s > best[1]:
            best = (o, s, iss)
    if best is None:
        raise RuntimeError("Başlık adayı yok.")
    return best
