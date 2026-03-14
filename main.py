from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import os
import uuid
import time
import threading

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ses dosyalarını belirli süre sonra temizle
def cleanup_old_files():
    while True:
        time.sleep(600)  # 10 dakikada bir kontrol
        now = time.time()
        for f in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > 1800:  # 30 dakika
                try:
                    os.remove(filepath)
                    print(f"Temizlendi: {f}")
                except:
                    pass

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

VOICES = {
    "Türkçe": [
        {"name": "tr-TR-AhmetNeural", "label": "Ahmet (Erkek)"},
        {"name": "tr-TR-EmelNeural", "label": "Emel (Kadın)"},
    ],
    "English (United States)": [
        {"name": "en-US-AnaNeural", "label": "Ana (Female)"},
        {"name": "en-US-AndrewMultilingualNeural", "label": "Andrew Multilingual (Male)"},
        {"name": "en-US-AndrewNeural", "label": "Andrew (Male)"},
        {"name": "en-US-AriaNeural", "label": "Aria (Female)"},
        {"name": "en-US-AvaMultilingualNeural", "label": "Ava Multilingual (Female)"},
        {"name": "en-US-AvaNeural", "label": "Ava (Female)"},
        {"name": "en-US-BrianMultilingualNeural", "label": "Brian Multilingual (Male)"},
        {"name": "en-US-BrianNeural", "label": "Brian (Male)"},
        {"name": "en-US-ChristopherNeural", "label": "Christopher (Male)"},
        {"name": "en-US-EmmaMultilingualNeural", "label": "Emma Multilingual (Female)"},
        {"name": "en-US-EmmaNeural", "label": "Emma (Female)"},
        {"name": "en-US-EricNeural", "label": "Eric (Male)"},
        {"name": "en-US-GuyNeural", "label": "Guy (Male)"},
        {"name": "en-US-JennyNeural", "label": "Jenny (Female)"},
        {"name": "en-US-MichelleNeural", "label": "Michelle (Female)"},
        {"name": "en-US-RogerNeural", "label": "Roger (Male)"},
        {"name": "en-US-SteffanNeural", "label": "Steffan (Male)"},
    ],
    "English (United Kingdom)": [
        {"name": "en-GB-LibbyNeural", "label": "Libby (Female)"},
        {"name": "en-GB-MaisieNeural", "label": "Maisie (Female)"},
        {"name": "en-GB-RyanNeural", "label": "Ryan (Male)"},
        {"name": "en-GB-SoniaNeural", "label": "Sonia (Female)"},
        {"name": "en-GB-ThomasNeural", "label": "Thomas (Male)"},
    ],
    "English (Australia)": [
        {"name": "en-AU-NatashaNeural", "label": "Natasha (Female)"},
        {"name": "en-AU-WilliamMultilingualNeural", "label": "William (Male)"},
    ],
    "English (Canada)": [
        {"name": "en-CA-ClaraNeural", "label": "Clara (Female)"},
        {"name": "en-CA-LiamNeural", "label": "Liam (Male)"},
    ],
    "English (India)": [
        {"name": "en-IN-NeerjaExpressiveNeural", "label": "Neerja Expressive (Female)"},
        {"name": "en-IN-NeerjaNeural", "label": "Neerja (Female)"},
        {"name": "en-IN-PrabhatNeural", "label": "Prabhat (Male)"},
    ],
    "Español (España)": [
        {"name": "es-ES-AlvaroNeural", "label": "Alvaro (Hombre)"},
        {"name": "es-ES-ElviraNeural", "label": "Elvira (Mujer)"},
        {"name": "es-ES-XimenaNeural", "label": "Ximena (Mujer)"},
    ],
    "Español (Estados Unidos)": [
        {"name": "es-US-AlonsoNeural", "label": "Alonso (Hombre)"},
        {"name": "es-US-PalomaNeural", "label": "Paloma (Mujer)"},
    ],
    "Español (México)": [
        {"name": "es-MX-DaliaNeural", "label": "Dalia (Mujer)"},
        {"name": "es-MX-JorgeNeural", "label": "Jorge (Hombre)"},
    ],
    "Español (Argentina)": [
        {"name": "es-AR-ElenaNeural", "label": "Elena (Mujer)"},
        {"name": "es-AR-TomasNeural", "label": "Tomas (Hombre)"},
    ],
    "Français (France)": [
        {"name": "fr-FR-DeniseNeural", "label": "Denise (Femme)"},
        {"name": "fr-FR-EloiseNeural", "label": "Eloise (Femme)"},
        {"name": "fr-FR-HenriNeural", "label": "Henri (Homme)"},
        {"name": "fr-FR-RemyMultilingualNeural", "label": "Remy Multilingual (Homme)"},
        {"name": "fr-FR-VivienneMultilingualNeural", "label": "Vivienne Multilingual (Femme)"},
    ],
    "Français (Canada)": [
        {"name": "fr-CA-AntoineNeural", "label": "Antoine (Homme)"},
        {"name": "fr-CA-JeanNeural", "label": "Jean (Homme)"},
        {"name": "fr-CA-SylvieNeural", "label": "Sylvie (Femme)"},
        {"name": "fr-CA-ThierryNeural", "label": "Thierry (Homme)"},
    ],
    "Deutsch (Deutschland)": [
        {"name": "de-DE-AmalaNeural", "label": "Amala (Weiblich)"},
        {"name": "de-DE-ConradNeural", "label": "Conrad (Männlich)"},
        {"name": "de-DE-FlorianMultilingualNeural", "label": "Florian Multilingual (Männlich)"},
        {"name": "de-DE-KatjaNeural", "label": "Katja (Weiblich)"},
        {"name": "de-DE-KillianNeural", "label": "Killian (Männlich)"},
        {"name": "de-DE-SeraphinaMultilingualNeural", "label": "Seraphina Multilingual (Weiblich)"},
    ],
    "Deutsch (Österreich)": [
        {"name": "de-AT-IngridNeural", "label": "Ingrid (Weiblich)"},
        {"name": "de-AT-JonasNeural", "label": "Jonas (Männlich)"},
    ],
    "Italiano": [
        {"name": "it-IT-DiegoNeural", "label": "Diego (Uomo)"},
        {"name": "it-IT-ElsaNeural", "label": "Elsa (Donna)"},
        {"name": "it-IT-GiuseppeMultilingualNeural", "label": "Giuseppe Multilingual (Uomo)"},
        {"name": "it-IT-IsabellaNeural", "label": "Isabella (Donna)"},
    ],
    "Português (Brasil)": [
        {"name": "pt-BR-AntonioNeural", "label": "Antonio (Masculino)"},
        {"name": "pt-BR-FranciscaNeural", "label": "Francisca (Feminino)"},
        {"name": "pt-BR-ThalitaMultilingualNeural", "label": "Thalita Multilingual (Feminino)"},
    ],
    "Português (Portugal)": [
        {"name": "pt-PT-DuarteNeural", "label": "Duarte (Masculino)"},
        {"name": "pt-PT-RaquelNeural", "label": "Raquel (Feminino)"},
    ],
    "Русский": [
        {"name": "ru-RU-DmitryNeural", "label": "Dmitry (Мужской)"},
        {"name": "ru-RU-SvetlanaNeural", "label": "Svetlana (Женский)"},
    ],
    "العربية (السعودية)": [
        {"name": "ar-SA-HamedNeural", "label": "Hamed (ذكر)"},
        {"name": "ar-SA-ZariyahNeural", "label": "Zariyah (أنثى)"},
    ],
    "العربية (الإمارات)": [
        {"name": "ar-AE-FatimaNeural", "label": "Fatima (أنثى)"},
        {"name": "ar-AE-HamdanNeural", "label": "Hamdan (ذكر)"},
    ],
    "العربية (مصر)": [
        {"name": "ar-EG-SalmaNeural", "label": "Salma (أنثى)"},
        {"name": "ar-EG-ShakirNeural", "label": "Shakir (ذكر)"},
    ],
    "中文 (普通话)": [
        {"name": "zh-CN-XiaoxiaoNeural", "label": "Xiaoxiao (女)"},
        {"name": "zh-CN-XiaoyiNeural", "label": "Xiaoyi (女)"},
        {"name": "zh-CN-YunjianNeural", "label": "Yunjian (男)"},
        {"name": "zh-CN-YunxiNeural", "label": "Yunxi (男)"},
        {"name": "zh-CN-YunxiaNeural", "label": "Yunxia (男)"},
        {"name": "zh-CN-YunyangNeural", "label": "Yunyang (男)"},
    ],
    "中文 (台湾)": [
        {"name": "zh-TW-HsiaoChenNeural", "label": "HsiaoChen (女)"},
        {"name": "zh-TW-HsiaoYuNeural", "label": "HsiaoYu (女)"},
        {"name": "zh-TW-YunJheNeural", "label": "YunJhe (男)"},
    ],
    "中文 (香港)": [
        {"name": "zh-HK-HiuGaaiNeural", "label": "HiuGaai (女)"},
        {"name": "zh-HK-HiuMaanNeural", "label": "HiuMaan (女)"},
        {"name": "zh-HK-WanLungNeural", "label": "WanLung (男)"},
    ],
    "日本語": [
        {"name": "ja-JP-KeitaNeural", "label": "Keita (男性)"},
        {"name": "ja-JP-NanamiNeural", "label": "Nanami (女性)"},
    ],
    "한국어": [
        {"name": "ko-KR-HyunsuMultilingualNeural", "label": "Hyunsu Multilingual (남성)"},
        {"name": "ko-KR-InJoonNeural", "label": "InJoon (남성)"},
        {"name": "ko-KR-SunHiNeural", "label": "SunHi (여성)"},
    ],
    "हिन्दी": [
        {"name": "hi-IN-MadhurNeural", "label": "Madhur (पुरुष)"},
        {"name": "hi-IN-SwaraNeural", "label": "Swara (महिला)"},
    ],
    "Nederlands": [
        {"name": "nl-NL-ColetteNeural", "label": "Colette (Vrouw)"},
        {"name": "nl-NL-FennaNeural", "label": "Fenna (Vrouw)"},
        {"name": "nl-NL-MaartenNeural", "label": "Maarten (Man)"},
    ],
    "Polski": [
        {"name": "pl-PL-MarekNeural", "label": "Marek (Mężczyzna)"},
        {"name": "pl-PL-ZofiaNeural", "label": "Zofia (Kobieta)"},
    ],
    "Svenska": [
        {"name": "sv-SE-MattiasNeural", "label": "Mattias (Man)"},
        {"name": "sv-SE-SofieNeural", "label": "Sofie (Kvinna)"},
    ],
    "Norsk": [
        {"name": "nb-NO-FinnNeural", "label": "Finn (Mann)"},
        {"name": "nb-NO-PernilleNeural", "label": "Pernille (Kvinne)"},
    ],
    "Dansk": [
        {"name": "da-DK-ChristelNeural", "label": "Christel (Kvinde)"},
        {"name": "da-DK-JeppeNeural", "label": "Jeppe (Mand)"},
    ],
    "Suomi": [
        {"name": "fi-FI-HarriNeural", "label": "Harri (Mies)"},
        {"name": "fi-FI-NooraNeural", "label": "Noora (Nainen)"},
    ],
}


@app.route("/")
def index():
    return render_template("index.html", voices=VOICES)


@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json()
    text = data.get("text", "").strip()
    voice = data.get("voice", "tr-TR-EmelNeural")
    rate = data.get("rate", "+0%")
    pitch = data.get("pitch", "+0Hz")
    volume = data.get("volume", "+0%")

    if not text:
        return jsonify({"error": "Metin boş olamaz"}), 400

    if len(text) > 25000:
        return jsonify({"error": "Metin 25000 karakterden uzun olamaz"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    async def generate():
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch, volume=volume
        )
        await communicate.save(filepath)

    try:
        asyncio.run(generate())
        
        # Dosyanın oluştuğunu kontrol et
        if not os.path.exists(filepath):
            return jsonify({"error": "Ses dosyası oluşturulamadı"}), 500
            
        return jsonify({"filename": filename})
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            return jsonify({"error": "Edge TTS servisine erişim engellendi. Lütfen tekrar deneyin."}), 503
        return jsonify({"error": f"Seslendirme hatası: {error_msg}"}), 500


@app.route("/audio/<filename>")
def serve_audio(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        # Dosya bulunamazsa yeniden oluşturmayı dene
        return jsonify({"error": "Ses dosyası bulunamadı. Lütfen tekrar seslendir."}), 404
    
    try:
        return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"Dosya okuma hatası: {str(e)}"}), 500


@app.route("/download/<filename>")
def download_audio(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Dosya bulunamadı"}), 404
    return send_file(filepath, mimetype="audio/mpeg", as_attachment=True, download_name=f"seslendirme_{filename}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)