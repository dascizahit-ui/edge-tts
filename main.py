from flask import Flask, render_template, request, send_file, jsonify, make_response
from werkzeug.utils import secure_filename
import edge_tts
import asyncio
import os
import re
import uuid
import time
import threading

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ses dosyalarını belirli süre sonra temizle
def cleanup_old_files():
    while True:
        time.sleep(600)
        now = time.time()
        for f in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > 1800:
                try:
                    os.remove(filepath)
                except Exception:
                    pass

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# ── Geçerli ses isimlerini doğrulama için set ──
VALID_VOICES = set()

VOICES = {
    "Turkish": [
        {"name": "tr-TR-AhmetNeural", "label": "Ahmet (Male)"},
        {"name": "tr-TR-EmelNeural", "label": "Emel (Female)"},
    ],
    "English (United States)": [
        {"name": "en-US-AnaNeural", "label": "Ana (Female)"},
        {"name": "en-US-AndrewMultilingualNeural", "label": "Andrew Multilingual (Male)"},
        {"name": "en-US-AndrewNeural", "label": "David (Male)"},
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
    "Spanish (Spain)": [
        {"name": "es-ES-AlvaroNeural", "label": "Alvaro (Male)"},
        {"name": "es-ES-ElviraNeural", "label": "Elvira (Female)"},
        {"name": "es-ES-XimenaNeural", "label": "Ximena (Female)"},
    ],
    "Spanish (United States)": [
        {"name": "es-US-AlonsoNeural", "label": "Alonso (Male)"},
        {"name": "es-US-PalomaNeural", "label": "Paloma (Female)"},
    ],
    "Spanish (Mexico)": [
        {"name": "es-MX-DaliaNeural", "label": "Dalia (Female)"},
        {"name": "es-MX-JorgeNeural", "label": "Jorge (Male)"},
    ],
    "Spanish (Argentina)": [
        {"name": "es-AR-ElenaNeural", "label": "Elena (Female)"},
        {"name": "es-AR-TomasNeural", "label": "Tomas (Male)"},
    ],
    "French (France)": [
        {"name": "fr-FR-DeniseNeural", "label": "Denise (Female)"},
        {"name": "fr-FR-EloiseNeural", "label": "Eloise (Female)"},
        {"name": "fr-FR-HenriNeural", "label": "Henri (Male)"},
        {"name": "fr-FR-RemyMultilingualNeural", "label": "Remy Multilingual (Male)"},
        {"name": "fr-FR-VivienneMultilingualNeural", "label": "Vivienne Multilingual (Female)"},
    ],
    "French (Canada)": [
        {"name": "fr-CA-AntoineNeural", "label": "Antoine (Male)"},
        {"name": "fr-CA-JeanNeural", "label": "Jean (Male)"},
        {"name": "fr-CA-SylvieNeural", "label": "Sylvie (Female)"},
        {"name": "fr-CA-ThierryNeural", "label": "Thierry (Male)"},
    ],
    "German (Germany)": [
        {"name": "de-DE-AmalaNeural", "label": "Amala (Female)"},
        {"name": "de-DE-ConradNeural", "label": "Conrad (Male)"},
        {"name": "de-DE-FlorianMultilingualNeural", "label": "Florian Multilingual (Male)"},
        {"name": "de-DE-KatjaNeural", "label": "Katja (Female)"},
        {"name": "de-DE-KillianNeural", "label": "Killian (Male)"},
        {"name": "de-DE-SeraphinaMultilingualNeural", "label": "Seraphina Multilingual (Female)"},
    ],
    "German (Austria)": [
        {"name": "de-AT-IngridNeural", "label": "Ingrid (Female)"},
        {"name": "de-AT-JonasNeural", "label": "Jonas (Male)"},
    ],
    "Italian": [
        {"name": "it-IT-DiegoNeural", "label": "Diego (Male)"},
        {"name": "it-IT-ElsaNeural", "label": "Elsa (Female)"},
        {"name": "it-IT-GiuseppeMultilingualNeural", "label": "Giuseppe Multilingual (Male)"},
        {"name": "it-IT-IsabellaNeural", "label": "Isabella (Female)"},
    ],
    "Portuguese (Brazil)": [
        {"name": "pt-BR-AntonioNeural", "label": "Antonio (Male)"},
        {"name": "pt-BR-FranciscaNeural", "label": "Francisca (Female)"},
        {"name": "pt-BR-ThalitaMultilingualNeural", "label": "Thalita Multilingual (Female)"},
    ],
    "Portuguese (Portugal)": [
        {"name": "pt-PT-DuarteNeural", "label": "Duarte (Male)"},
        {"name": "pt-PT-RaquelNeural", "label": "Raquel (Female)"},
    ],
    "Russian": [
        {"name": "ru-RU-DmitryNeural", "label": "Dmitry (Male)"},
        {"name": "ru-RU-SvetlanaNeural", "label": "Svetlana (Female)"},
    ],
    "Arabic (Saudi Arabia)": [
        {"name": "ar-SA-HamedNeural", "label": "Hamed (Male)"},
        {"name": "ar-SA-ZariyahNeural", "label": "Zariyah (Female)"},
    ],
    "Arabic (UAE)": [
        {"name": "ar-AE-FatimaNeural", "label": "Fatima (Female)"},
        {"name": "ar-AE-HamdanNeural", "label": "Hamdan (Male)"},
    ],
    "Arabic (Egypt)": [
        {"name": "ar-EG-SalmaNeural", "label": "Salma (Female)"},
        {"name": "ar-EG-ShakirNeural", "label": "Shakir (Male)"},
    ],
    "Chinese (Mandarin)": [
        {"name": "zh-CN-XiaoxiaoNeural", "label": "Xiaoxiao (Female)"},
        {"name": "zh-CN-XiaoyiNeural", "label": "Xiaoyi (Female)"},
        {"name": "zh-CN-YunjianNeural", "label": "Yunjian (Male)"},
        {"name": "zh-CN-YunxiNeural", "label": "Yunxi (Male)"},
        {"name": "zh-CN-YunxiaNeural", "label": "Yunxia (Male)"},
        {"name": "zh-CN-YunyangNeural", "label": "Yunyang (Male)"},
    ],
    "Chinese (Taiwan)": [
        {"name": "zh-TW-HsiaoChenNeural", "label": "HsiaoChen (Female)"},
        {"name": "zh-TW-HsiaoYuNeural", "label": "HsiaoYu (Female)"},
        {"name": "zh-TW-YunJheNeural", "label": "YunJhe (Male)"},
    ],
    "Chinese (Hong Kong)": [
        {"name": "zh-HK-HiuGaaiNeural", "label": "HiuGaai (Female)"},
        {"name": "zh-HK-HiuMaanNeural", "label": "HiuMaan (Female)"},
        {"name": "zh-HK-WanLungNeural", "label": "WanLung (Male)"},
    ],
    "Japanese": [
        {"name": "ja-JP-KeitaNeural", "label": "Keita (Male)"},
        {"name": "ja-JP-NanamiNeural", "label": "Nanami (Female)"},
    ],
    "Korean": [
        {"name": "ko-KR-HyunsuMultilingualNeural", "label": "Hyunsu Multilingual (Male)"},
        {"name": "ko-KR-InJoonNeural", "label": "InJoon (Male)"},
        {"name": "ko-KR-SunHiNeural", "label": "SunHi (Female)"},
    ],
    "Hindi": [
        {"name": "hi-IN-MadhurNeural", "label": "Madhur (Male)"},
        {"name": "hi-IN-SwaraNeural", "label": "Swara (Female)"},
    ],
    "Dutch": [
        {"name": "nl-NL-ColetteNeural", "label": "Colette (Female)"},
        {"name": "nl-NL-FennaNeural", "label": "Fenna (Female)"},
        {"name": "nl-NL-MaartenNeural", "label": "Maarten (Male)"},
    ],
    "Polish": [
        {"name": "pl-PL-MarekNeural", "label": "Marek (Male)"},
        {"name": "pl-PL-ZofiaNeural", "label": "Zofia (Female)"},
    ],
    "Swedish": [
        {"name": "sv-SE-MattiasNeural", "label": "Mattias (Male)"},
        {"name": "sv-SE-SofieNeural", "label": "Sofie (Female)"},
    ],
    "Norwegian": [
        {"name": "nb-NO-FinnNeural", "label": "Finn (Male)"},
        {"name": "nb-NO-PernilleNeural", "label": "Pernille (Female)"},
    ],
    "Danish": [
        {"name": "da-DK-ChristelNeural", "label": "Christel (Female)"},
        {"name": "da-DK-JeppeNeural", "label": "Jeppe (Male)"},
    ],
    "Finnish": [
        {"name": "fi-FI-HarriNeural", "label": "Harri (Male)"},
        {"name": "fi-FI-NooraNeural", "label": "Noora (Female)"},
    ],
}

# Geçerli ses isimlerini topla
for lang_voices in VOICES.values():
    for v in lang_voices:
        VALID_VOICES.add(v["name"])


# ── Doğrulama yardımcıları ──
def validate_rate(rate):
    if re.match(r'^[+-]\d{1,3}%$', rate):
        val = int(rate[:-1])
        return -50 <= val <= 100
    return False

def validate_pitch(pitch):
    if re.match(r'^[+-]\d{1,3}Hz$', pitch):
        val = int(pitch[:-2])
        return -50 <= val <= 50
    return False

def validate_volume(volume):
    if re.match(r'^[+-]\d{1,3}%$', volume):
        val = int(volume[:-1])
        return -50 <= val <= 50
    return False


@app.route("/")
def index():
    return render_template("index.html", voices=VOICES)


@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Geçersiz istek formatı"}), 400

    text = data.get("text", "").strip()
    voice = data.get("voice", "tr-TR-EmelNeural")
    rate = data.get("rate", "+0%")
    pitch = data.get("pitch", "+0Hz")
    volume = data.get("volume", "+0%")

    # ── Doğrulamalar ──
    if not text:
        return jsonify({"error": "Metin boş olamaz"}), 400

    if len(text) > 25000:
        return jsonify({"error": "Metin 25000 karakterden uzun olamaz"}), 400

    if voice not in VALID_VOICES:
        return jsonify({"error": "Geçersiz ses seçimi"}), 400

    if not validate_rate(rate):
        return jsonify({"error": "Geçersiz hız değeri"}), 400

    if not validate_pitch(pitch):
        return jsonify({"error": "Geçersiz ton değeri"}), 400

    if not validate_volume(volume):
        return jsonify({"error": "Geçersiz ses seviyesi değeri"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    async def generate():
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch, volume=volume
        )
        await communicate.save(filepath)

    # Güvenli asyncio — her istekte temiz event loop
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate())
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            return jsonify({"error": "Edge TTS servisine erişim engellendi. Lütfen tekrar deneyin."}), 503
        return jsonify({"error": f"Seslendirme hatası: {error_msg}"}), 500
    finally:
        loop.close()

    if not os.path.exists(filepath):
        return jsonify({"error": "Ses dosyası oluşturulamadı"}), 500

    file_size = os.path.getsize(filepath)
    return jsonify({"filename": filename, "size": file_size})


@app.route("/audio/<filename>")
def serve_audio(filename):
    filename = secure_filename(filename)
    if not filename:
        return jsonify({"error": "Geçersiz dosya adı"}), 400

    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Ses dosyası bulunamadı. Lütfen tekrar seslendir."}), 404

    try:
        return send_file(filepath, mimetype="audio/mpeg", as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"Dosya okuma hatası: {str(e)}"}), 500


@app.route("/download/<filename>")
def download_audio(filename):
    filename = secure_filename(filename)
    if not filename:
        return jsonify({"error": "Geçersiz dosya adı"}), 400

    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Dosya bulunamadı"}), 404

    try:
        file_size = os.path.getsize(filepath)
        response = make_response(
            send_file(
                filepath,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name=f"sesforge_{filename}",
            )
        )
        response.headers["Content-Length"] = file_size
        response.headers["Cache-Control"] = "no-cache"
        return response
    except Exception as e:
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)