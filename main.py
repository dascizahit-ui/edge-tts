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
    "English": [
        {"name": "en-US-GuyNeural", "label": "Guy (Male)"},
        {"name": "en-US-JennyNeural", "label": "Jenny (Female)"},
        {"name": "en-US-AriaNeural", "label": "Aria (Female)"},
        {"name": "en-US-BrianNeural", "label": "Brian (Male)"},
        {"name": "en-US-EmmaNeural", "label": "Emma (Female)"},
        {"name": "en-US-AndrewNeural", "label": "Andrew (Male)"},
        {"name": "en-US-AvaNeural", "label": "Ava (Female)"},
        {"name": "en-GB-SoniaNeural", "label": "Sonia (British Female)"},
        {"name": "en-GB-RyanNeural", "label": "Ryan (British Male)"},
        {"name": "en-GB-LibbyNeural", "label": "Libby (British Female)"},
        {"name": "en-GB-ThomasNeural", "label": "Thomas (British Male)"},
    ],
    "Deutsch": [
        {"name": "de-DE-ConradNeural", "label": "Conrad (Männlich)"},
        {"name": "de-DE-KatjaNeural", "label": "Katja (Weiblich)"},
    ],
    "Français": [
        {"name": "fr-FR-HenriNeural", "label": "Henri (Homme)"},
        {"name": "fr-FR-DeniseNeural", "label": "Denise (Femme)"},
    ],
    "Español": [
        {"name": "es-ES-AlvaroNeural", "label": "Alvaro (Hombre)"},
        {"name": "es-ES-ElviraNeural", "label": "Elvira (Mujer)"},
    ],
    "Spanish (United States)": [
        {"name": "es-US-AlonsoNeural", "label": "Alonso (Male)"},
        {"name": "es-US-PalomaNeural", "label": "Paloma (Female)"},
    ],
    "Italiano": [
        {"name": "it-IT-DiegoNeural", "label": "Diego (Uomo)"},
        {"name": "it-IT-ElsaNeural", "label": "Elsa (Donna)"},
    ],
    "Português": [
        {"name": "pt-BR-AntonioNeural", "label": "Antonio (Masculino)"},
        {"name": "pt-BR-FranciscaNeural", "label": "Francisca (Feminino)"},
    ],
    "Русский": [
        {"name": "ru-RU-DmitryNeural", "label": "Dmitry (Мужской)"},
        {"name": "ru-RU-SvetlanaNeural", "label": "Svetlana (Женский)"},
    ],
    "العربية": [
        {"name": "ar-SA-HamedNeural", "label": "Hamed (ذكر)"},
        {"name": "ar-SA-ZariyahNeural", "label": "Zariyah (أنثى)"},
    ],
    "中文": [
        {"name": "zh-CN-YunxiNeural", "label": "Yunxi (男)"},
        {"name": "zh-CN-XiaoxiaoNeural", "label": "Xiaoxiao (女)"},
    ],
    "日本語": [
        {"name": "ja-JP-KeitaNeural", "label": "Keita (男性)"},
        {"name": "ja-JP-NanamiNeural", "label": "Nanami (女性)"},
    ],
    "한국어": [
        {"name": "ko-KR-InJoonNeural", "label": "InJoon (남성)"},
        {"name": "ko-KR-SunHiNeural", "label": "SunHi (여성)"},
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
