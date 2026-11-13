"""Tek dosyalık yayın: futbol/index.html -> tek bir index.html

Çalıştır:  python3 futbol/build_crazygames.py        -> futbol/crazygames/index.html (CrazyGames)
           python3 futbol/build_crazygames.py web    -> docs/oyun/index.html (telefonda oynamak için, GitHub Pages)
           python3 futbol/build_crazygames.py android -> mobil/www/index.html (Google Play uygulaması, AdMob)
- three.js ve yazı tipleri dosyanın içine gömülür (dış bağlantı yok, sadece CrazyGames SDK)
- window.__CG açılır: gerçek reklamlar, güvenli takım/lig isimleri
- CrazyGames zip kabul etmediği için tek bir index.html üretilir; panele sadece bu dosya sürüklenir
"""
import base64, json, os, re, shutil, sys

MODE = sys.argv[1] if len(sys.argv) > 1 else 'cg'
WEB, APP = MODE == 'web', MODE == 'android'

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'oyun') if WEB else os.path.join(HERE, '..', 'mobil', 'www') if APP else os.path.join(HERE, 'crazygames')
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
if APP:  # Capacitor eklentileri (AdMob, App) + reklam kimlikleri
    M = os.path.join(HERE, '..', 'mobil')
    cap = open(os.path.join(M, 'cap.js'), encoding='utf-8').read()
    assert '</script' not in cap
    ids = json.load(open(os.path.join(M, 'admob.json'), encoding='utf-8'))
    sx = os.path.join(M, 'android', 'app', 'src', 'main', 'res', 'values', 'strings.xml')
    if os.path.exists(sx):  # AdMob uygulama kimliğini Android ayarına yaz
        t = open(sx, encoding='utf-8').read()
        t = re.sub(r'(<string name="admob_app_id">)[^<]*(</string>)', lambda m: m.group(1) + ids['app'] + m.group(2), t)
        open(sx, 'w', encoding='utf-8').write(t)
    pre = '<script>window.__APP = true; window.__ADMOB = ' + json.dumps({'reward': ids['reward'], 'inter': ids['inter']}) + ';</script>\n<script>\n' + cap + '\n</script>\n'
elif WEB:
    pre = ''
else:
    pre = SDK + '\n<script>window.__CG = true;</script>\n'

html = re.sub(r'<link rel="preconnect"[^>]*>\n?', '', html)
html, n1 = re.subn(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">', lambda m: '<style>\n' + css + '</style>', html)
html, n2 = re.subn(r'<script src="https://cdn\.jsdelivr\.net/npm/three@[^"]*"></script>',
                   lambda m: pre + '<script>\n' + three + '\n</script>', html)
assert n1 == 1 and n2 == 1, (n1, n2)
if WEB:
    html = html.replace('<title>Yıldız Yolu</title>', '<title>Yıldız Yolu</title>\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n<meta name="apple-mobile-web-app-title" content="Yıldız Yolu">\n<meta name="theme-color" content="#080e0c">\n<link rel="apple-touch-icon" href="icon-180.png">\n<link rel="icon" href="icon-180.png">\n<link rel="manifest" href="manifest.json">', 1)
else:
    html = html.replace('<title>Yıldız Yolu</title>', '<title>Star Path: Football Career</title>', 1)
if not html.lstrip().lower().startswith('<!doctype'):
    html = re.sub(r'<meta name="claude:[^>]*>\n?', '', html)
    # ilk iki <style> bloğu (yazı tipleri + oyun stili) head'e gider
    first = html.index('</style>') + len('</style>')
    second = html.index('</style>', first) + len('</style>')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + html[:second] + '\n</head>\n<body>\n' + html[second:] + '\n</body>\n</html>\n')

if APP:  # uygulamada iki parmakla yakınlaştırma kapalı
    html = html.replace('viewport-fit=cover">', 'viewport-fit=cover,user-scalable=no">', 1)

if os.path.isdir(OUT):
    for f in os.listdir(OUT):
        if f == 'index.html':
            os.remove(os.path.join(OUT, f))
os.makedirs(OUT, exist_ok=True)
dst = os.path.join(OUT, 'index.html')
open(dst, 'w', encoding='utf-8').write(html)
print('ok', dst, round(os.path.getsize(dst) / 1024), 'KB')
