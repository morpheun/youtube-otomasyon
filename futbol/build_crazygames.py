"""CrazyGames yayın paketi: futbol/index.html -> futbol/crazygames/ + futbol/crazygames.zip

Çalıştır:  python3 futbol/build_crazygames.py
- three.js ve yazı tipleri pakete gömülür (dış bağlantı yok, sadece CrazyGames SDK)
- window.__CG açılır: gerçek reklamlar, güvenli takım/lig isimleri
"""
import os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'crazygames')
SDK = '<script src="https://sdk.crazygames.com/crazygames-sdk-v3.js"></script>'

src = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
html = src
html = re.sub(r'<link rel="preconnect"[^>]*>\n?', '', html)
html, n1 = re.subn(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">', '<link rel="stylesheet" href="fonts.css">', html)
html, n2 = re.subn(r'<script src="https://cdn\.jsdelivr\.net/npm/three@[^"]*"></script>', SDK + '\n<script>window.__CG = true;</script>\n<script src="three.min.js"></script>', html)
assert n1 == 1 and n2 == 1, (n1, n2)
if not html.lstrip().lower().startswith('<!doctype'):
    html = re.sub(r'<meta name="claude:[^>]*>\n?', '', html)
    cut = html.index('</style>') + len('</style>')
    html = ('<!doctype html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + html[:cut] + '\n</head>\n<body>\n' + html[cut:] + '\n</body>\n</html>\n')

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, 'fonts'))
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
V = os.path.join(HERE, 'vendor')
shutil.copy(os.path.join(V, 'three.min.js'), OUT)
shutil.copy(os.path.join(V, 'fonts.css'), OUT)
for f in os.listdir(os.path.join(V, 'fonts')):
    shutil.copy(os.path.join(V, 'fonts', f), os.path.join(OUT, 'fonts'))

zp = os.path.join(HERE, 'crazygames.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, OUT))
print('ok', zp, round(os.path.getsize(zp) / 1024), 'KB')
