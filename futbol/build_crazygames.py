"""CrazyGames yayın dosyası: futbol/index.html -> futbol/crazygames/index.html (TEK DOSYA)

Çalıştır:  python3 futbol/build_crazygames.py
- three.js ve yazı tipleri dosyanın içine gömülür (dış bağlantı yok, sadece CrazyGames SDK)
- window.__CG açılır: gerçek reklamlar, güvenli takım/lig isimleri
- CrazyGames zip kabul etmediği için tek bir index.html üretilir; panele sadece bu dosya sürüklenir
"""
import base64, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'crazygames')
V = os.path.join(HERE, 'vendor')
SDK = '<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>'

html = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()

# yazı tipleri: data URI olarak göm
css = open(os.path.join(V, 'fonts.css'), encoding='utf-8').read()
def inline_font(m):
    data = open(os.path.join(V, m.group(1)), 'rb').read()
    return 'url(data:font/woff2;base64,' + base64.b64encode(data).decode() + ')'
css = re.sub(r'url\((fonts/[^)]+)\)', inline_font, css)

three = open(os.path.join(V, 'three.min.js'), encoding='utf-8').read()
assert '</script' not in three

html = re.sub(r'<link rel="preconnect"[^>]*>\n?', '', html)
html, n1 = re.subn(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">', lambda m: '<style>\n' + css + '</style>', html)
html, n2 = re.subn(r'<script src="https://cdn\.jsdelivr\.net/npm/three@[^"]*"></script>',
                   lambda m: SDK + '\n<script>window.__CG = true;</script>\n<script>\n' + three + '\n</script>', html)
assert n1 == 1 and n2 == 1, (n1, n2)
html = html.replace('<title>Yıldız Yolu</title>', '<title>Star Path: Football Career</title>', 1)
if not html.lstrip().lower().startswith('<!doctype'):
    html = re.sub(r'<meta name="claude:[^>]*>\n?', '', html)
    # ilk iki <style> bloğu (yazı tipleri + oyun stili) head'e gider
    first = html.index('</style>') + len('</style>')
    second = html.index('</style>', first) + len('</style>')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + html[:second] + '\n</head>\n<body>\n' + html[second:] + '\n</body>\n</html>\n')

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
dst = os.path.join(OUT, 'index.html')
open(dst, 'w', encoding='utf-8').write(html)
print('ok', dst, round(os.path.getsize(dst) / 1024), 'KB')
