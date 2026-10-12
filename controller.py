#!/usr/bin/env python3
import os
import uuid
import asyncio
import shutil
import json

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from psychologist_ai import get_psychologist_advice, generate_speech
from emotion_module import analyze_emotion


app = Flask(__name__, static_folder="static", template_folder=".")
socketio = SocketIO(app, cors_allowed_origins="*")

AUDIO_DIR = os.path.join(app.static_folder, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

CHAT_MEMORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "chat_memory.json")
AI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai")
os.makedirs(AI_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/audio/<path:fname>")
def audio(fname):
    return send_from_directory(AUDIO_DIR, fname)


@app.route("/ai/reset_chat", methods=["POST"])
def reset_chat():
    try:
        with open(CHAT_MEMORY_PATH, "w") as f:
            f.write("[]")
        return "Chat reset", 200
    except Exception as e:
        print(f"Error resetting chat: {e}")
        return f"Error: {e}", 500


@app.route("/ai/chat_memory.json")
def chat_memory():
    if os.path.exists(CHAT_MEMORY_PATH):
        return send_from_directory(os.path.dirname(CHAT_MEMORY_PATH), "chat_memory.json")
    return "[]", 200


@app.route("/haru/<path:filename>")
def serve_haru_files(filename):
    haru_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haru")
    return send_from_directory(haru_path, filename)


@socketio.on("user_input")
def on_user(data):
    text = data.get("text", "").strip()
    if not text:
        return

    # Update chat memory
    try:
        with open(CHAT_MEMORY_PATH, "r") as f:
            chat_memory = json.load(f)
    except Exception:
        chat_memory = []

    chat_memory.append({"role": "user", "text": text})

    # Analyze emotion from frame
    frame_b64 = data.get("frame", "")
    emotion = analyze_emotion(frame_b64)

    # Get advice
    advice = get_psychologist_advice(emotion, text)

    # Append assistant response
    chat_memory.append({"role": "assistant", "text": advice})

    with open(CHAT_MEMORY_PATH, "w") as f:
        json.dump(chat_memory, f)

    # Generate and serve audio
    mp3_tmp = asyncio.run(generate_speech(advice))
    fname = f"{uuid.uuid4().hex}.mp3"
    dst = os.path.join(AUDIO_DIR, fname)
    shutil.move(mp3_tmp, dst)

    emit("bot_reply", {
        "advice": advice,
        "audio": f"/static/audio/{fname}",
        "emotion": emotion
    })


if __name__ == "__main__":
    print("Server running at http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
