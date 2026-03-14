# SesForge — Edge TTS Seslendirme Uygulaması

Microsoft Edge TTS altyapısını kullanarak metni sese dönüştüren web uygulaması.

## Özellikler

- 12 dil, 24+ ses desteği (Türkçe, İngilizce, Almanca, Fransızca, İspanyolca, İtalyanca, Portekizce, Rusça, Arapça, Çince, Japonca, Korece)
- Hız, ton ve ses seviyesi ayarları
- Yerleşik ses oynatıcı ve dalga formu görselleştirmesi
- MP3 indirme
- Otomatik dosya temizleme (10 dakika sonra)
- Karanlık tema, mobil uyumlu arayüz

## Replit'te Çalıştırma

1. Replit'te yeni bir **Python** projesi oluşturun
2. Tüm dosyaları projeye yükleyin:
   - `app.py`
   - `requirements.txt`
   - `.replit`
   - `templates/index.html`
   - `static/style.css`
   - `static/app.js`
3. **Run** butonuna basın
4. Uygulama otomatik olarak başlayacaktır

## Yerel Çalıştırma

```bash
pip install -r requirements.txt
python app.py
```

Tarayıcınızda `http://localhost:5000` adresine gidin.

## Klavye Kısayolu

- `Ctrl + Enter` — Seslendir
