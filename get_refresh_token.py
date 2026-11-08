"""YouTube yükleme izni için BİR KEZ kendi bilgisayarında çalıştır.

  pip install google-auth-oauthlib
  python get_refresh_token.py client_secret.json

Tarayıcı açılır -> kanalının bağlı olduğu Google hesabıyla giriş yap -> izin ver.
Ekrana yazılan 3 değeri GitHub > Settings > Secrets and variables > Actions'a ekle.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

path = sys.argv[1] if len(sys.argv) > 1 else "client_secret.json"
flow = InstalledAppFlow.from_client_secrets_file(path, SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

info = json.load(open(path))
info = info.get("installed") or info.get("web")
print("\nAşağıdakileri GitHub Secrets'a ekle:\n")
print(f"YT_CLIENT_ID      = {info['client_id']}")
print(f"YT_CLIENT_SECRET  = {info['client_secret']}")
print(f"YT_REFRESH_TOKEN  = {creds.refresh_token}")
