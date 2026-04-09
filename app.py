
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import json
from emotion_engine import EmotionAnalyzer
from voice_engine import VoiceEngine

app = Flask(__name__)
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

emotion_analyzer = EmotionAnalyzer()
voice_engine = VoiceEngine(audio_dir=AUDIO_DIR)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/synthesize", methods=["POST"])
def synthesize():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400

    if len(text) > 500:
        return jsonify({"error": "Text too long (max 500 characters)"}), 400

    # Step 1: Analyze emotion
    emotion_result = emotion_analyzer.analyze(text)

    # Step 2: Synthesize speech with modulated voice
    filename = f"audio_{uuid.uuid4().hex[:12]}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    success, error_msg = voice_engine.synthesize(
        text=text,
        emotion=emotion_result,
        output_path=filepath
    )

    if not success:
        return jsonify({"error": f"Audio generation failed: {error_msg}"}), 500

    return jsonify({
        "audio_url": f"/static/audio/{filename}",
        "emotion": emotion_result["label"],
        "confidence": round(emotion_result["confidence"] * 100, 1),
        "intensity": emotion_result["intensity"],
        "voice_params": emotion_result["voice_params"],
        "scores": emotion_result["scores"]
    })


@app.route("/api/emotions", methods=["GET"])
def get_emotions():
    """Return emotion metadata for UI display"""
    return jsonify(emotion_analyzer.get_emotion_metadata())


@app.route("/static/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
