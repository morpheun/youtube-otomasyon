// Oyunun kullandığı Capacitor eklentileri: tek dosyaya paketlenip www/index.html içine gömülür
import { Capacitor } from '@capacitor/core';
import { AdMob } from '@capacitor-community/admob';
import { App } from '@capacitor/app';
window.__cap = { Capacitor, AdMob, App, native: Capacitor.isNativePlatform() };
