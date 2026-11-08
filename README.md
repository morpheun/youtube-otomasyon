# Otomatik Hikaye Animasyonu Shorts → YouTube

Her gün 2 kez (10:17 ve 19:23, Türkiye saati) kendiliğinden:

1. **Senaryo** – Claude, daha önce anlatılmamış ~45 saniyelik Türkçe bir hikaye yazar (7 sahne, başlık, açıklama, etiketler).
2. **Seslendirme** – Türkçe yapay zekâ sesi (`tr-TR-AhmetNeural`, edge-tts, ücretsiz).
3. **Görseller** – Her sahne için 1080×1920 animasyon tarzı görsel (Pollinations / FLUX). Karakter tarifi her sahnede aynı tutulur.
4. **Montaj** – ffmpeg ile kamera hareketleri (yakınlaşma/kaydırma), geçişler, kelime kelime vurgulanan büyük altyazılar, isteğe bağlı arka plan müziği.
5. **Yükleme** – YouTube Data API ile kanala `#shorts` olarak yükler.

Hepsi **GitHub Actions** üzerinde çalışır: bilgisayarın kapalı olsa bile devam eder, sunucu ücreti yoktur.

---

## Kurulum (bir kerelik, ~20 dk)

### 1) Kodu GitHub'a koy
GitHub'da **özel (private)** yeni bir depo aç ve bu klasörü oraya yükle:

```bash
git remote add origin https://github.com/KULLANICI_ADIN/youtube-otomasyon.git
```

```bash
git push -u origin main
```

### 2) Anthropic API anahtarı (senaryo için)
<https://console.anthropic.com> → API Keys → yeni anahtar. Video başına maliyet birkaç sent civarındadır.

### 3) Pollinations anahtarı (görseller için – önerilir)
<https://enter.pollinations.ai> → ücretsiz hesap → API key. Anahtar olmadan da eski ücretsiz uç nokta denenir ama yavaş ve sınırlıdır.

### 4) YouTube yükleme izni (Google Cloud)
1. <https://console.cloud.google.com> → yeni proje oluştur.
2. **APIs & Services → Library → "YouTube Data API v3" → Enable.**
3. **OAuth consent screen**: User type *External*, uygulama adı ver, kendi e-postanı ekle.
   Sonra **Publishing status → "In production"** yap. (*Testing* modunda kalırsa izin 7 günde bir düşer ve yüklemeler durur. Doğrulanmamış uygulama uyarısı çıkar; kendi hesabın için "Devam et" demen yeterli.)
4. **Credentials → Create credentials → OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URIs → **Add URI** → `https://developers.google.com/oauthplayground`
   - **Create** → çıkan **Client ID** ve **Client secret**'ı bir kenara kopyala.
5. <https://developers.google.com/oauthplayground> adresini aç (bilgisayara hiçbir şey kurmak gerekmez):
   - Sağ üstteki **⚙️ dişli** → **Use your own OAuth credentials** kutusunu işaretle → Client ID ve Client secret'ı yapıştır.
   - Soldaki kutuya `https://www.googleapis.com/auth/youtube.upload` yaz → **Authorize APIs**.
   - **@morpheunn kanalının bağlı olduğu Google hesabını** seç → "Google bu uygulamayı doğrulamadı" çıkarsa **Gelişmiş → Devam et** → İzin ver.
   - **Exchange authorization code for tokens** düğmesine bas → çıkan **Refresh token**'ı kopyala.

   (Alternatif: Python biliyorsan *Desktop app* türünde istemci oluşturup `python get_refresh_token.py client_secret.json` da çalıştırabilirsin.)

### 5) GitHub Secrets
Depo → **Settings → Secrets and variables → Actions → New repository secret**:

| Ad | Değer |
|---|---|
| `ANTHROPIC_API_KEY` | 2. adımdaki anahtar |
| `POLLINATIONS_API_KEY` | 3. adımdaki anahtar |
| `YT_CLIENT_ID` | 4. adımdaki Client ID |
| `YT_CLIENT_SECRET` | 4. adımdaki Client secret |
| `YT_REFRESH_TOKEN` | 5. adımdaki Refresh token |

### 6) İlk deneme
Depo → **Actions → Otomatik Shorts → Run workflow**. "YouTube'a yüklensin mi?" kutusunu kaldırırsan sadece video üretir; videoyu çalışma sayfasının altındaki **Artifacts**'tan indirip kontrol edebilirsin. Beğenirsen kutu işaretli tekrar çalıştır. Bundan sonra günde 2 kez kendisi çalışır.

---

## ⚠️ "Herkese açık" yayın hakkında önemli not
YouTube, **denetimden (audit) geçmemiş** Google Cloud projelerinden API ile yüklenen videoları otomatik olarak **gizli (private)** yapar. Yani ilk başta videolar kanala gizli düşer ve YouTube Studio'dan "Herkese açık" yapman gerekir.

Tam otomatik herkese açık yayın için projeni bir kez denetime gönder:
<https://support.google.com/youtube/contact/yt_api_form> → "YouTube API Services – Audit and Quota Extension Form". Onaylandıktan sonra hiçbir şeyi değiştirmen gerekmez; `config.json`'da `youtube_privacy` zaten `public`.

## Ayarlar (`config.json`)
- `story_themes` – hikaye türleri (her videoda rastgele biri seçilir)
- `art_styles` – çizim tarzları (Pixar benzeri 3D, Ghibli benzeri anime, suluboya…)
- `target_seconds`, `scene_count` – süre ve sahne sayısı
- `tts_voice` – ses: `tr-TR-AhmetNeural` (erkek) veya `tr-TR-EmelNeural` (kadın); `tts_rate` konuşma hızı
- `youtube_privacy` – `public` / `unlisted` / `private`

Saatleri değiştirmek için `.github/workflows/shorts.yml` içindeki `cron` satırlarını düzenle (saatler UTC; Türkiye = UTC+3).

Arka plan müziği istiyorsan `assets/music/` içine telifsiz `.mp3` dosyaları koy (ör. YouTube Studio Ses Kitaplığı).

## Kendi bilgisayarında çalıştırma

```bash
pip install -r requirements.txt
```

```bash
python main.py --no-upload
```

(ffmpeg kurulu olmalı. `ANTHROPIC_API_KEY` ve isteğe bağlı `POLLINATIONS_API_KEY` ortam değişkenleri gerekir.)

## Bilmen gerekenler
- **Kota:** YouTube API günlük 10.000 birim verir, bir yükleme 1.600 birim → günde en fazla ~6 video. Günde 2 sorunsuz.
- **Para kazanma:** YouTube, birbirinin aynısı seri üretim içeriklere karşı YPP kurallarını sıkılaştırdı. Hikayeler her seferinde farklı yazılıyor, ama arada kendi dokunuşunu (özel seri, karakter, seslendirme) eklemek kanal için daha güvenli olur.
- Videolar YouTube'a "yapay zekâ ile üretilmiş içerik" (`containsSyntheticMedia`) olarak beyan edilir.
- edge-tts resmi olmayan bir Microsoft servisidir; bir gün çalışmazsa iş hata verir, video yüklenmez (yarım video yayınlanmaz).
