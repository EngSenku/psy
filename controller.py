#!/usr/bin/env python3
import os, uuid, asyncio, base64, cv2, numpy as np, shutil, json
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from deepface import DeepFace
from psychologist_ai import get_psychologist_advice, generate_speech
from emotion_module import analyze_emotion

app = Flask(__name__, static_folder="static", template_folder=".")
socketio = SocketIO(app, cors_allowed_origins="*")

AUDIO_DIR = os.path.join(app.static_folder, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/audio/<path:fname>")
def audio(fname):
    return send_from_directory(AUDIO_DIR, fname)

@app.route("/ai/reset_chat", methods=["POST"])
def reset_chat():
    chat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_memory.json")
    print("Attempting to reset chat at:", chat_path)
    try:
        # Create the file if it does not exist
        if not os.path.exists(chat_path):
            with open(chat_path, "w") as f:
                f.write("[]")
        # Reset chat content to an empty array
        with open(chat_path, "w") as f:
            f.write("[]")
        print("Chat reset successfully")
        return "Chat reset", 200
    except Exception as e:
        print(f"Error resetting chat: {e}")
        return f"Error: {e}", 500

@app.route("/ai/chat_memory.json")
def chat_memory():
    chat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai/chat_memory.json")
    if os.path.exists(chat_path):
        return send_from_directory(os.path.dirname(chat_path), "chat_memory.json")
    return "[]", 200  # Return an empty array if the file doesn't exist

@app.route("/haru/<path:filename>")
def serve_haru_files(filename):
    haru_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haru")
    return send_from_directory(haru_path, filename)

def decode_frame(data_url: str):
    try:
        _, b64 = data_url.split(",", 1)
        arr = np.frombuffer(base64.b64decode(b64), np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except:
        return None

@socketio.on("user_input")
def on_user(data):
    text = data.get("text", "").strip()
    frame = data.get("frame", "")
    if not text:
        return

    print(f"[SERVER] User text: {text!r}")

    # Update chat memory
    chat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai/chat_memory.json")
    try:
        with open(chat_path, "r") as f:
            chat_memory = json.load(f)
    except:
        chat_memory = []

    # Append the user's input
    chat_memory.append({"role": "user", "text": text})

# 1) emotion
    # The 'frame' variable already contains the base64 string from the client
    frame_b64 = data.get("frame", "") # Get the base64 string
    
    # 🚨 CALL THE DEDICATED FUNCTION HERE 🚨
    emotion = analyze_emotion(frame_b64)
    
    # The rest of the commented-out logic is removed/replaced
    # if img is not None:
    #     try:
    #         res = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
    #         emotion = res[0]['dominant_emotion']
    #     except Exception as e:
    #         print("DeepFace error:", e)
            
    print(f"[SERVER] Detected emotion: {emotion}")

    # 2) advice
    advice = get_psychologist_advice(emotion, text)
    print(f"[SERVER] Advice: {advice}")

    # Append the AI response
    chat_memory.append({"role": "assistant", "text": advice})

    with open(chat_path, "w") as f:
        json.dump(chat_memory, f)

    # 3) TTS → MP3 file
    mp3_tmp = asyncio.run(generate_speech(advice))
    fname   = f"{uuid.uuid4().hex}.mp3"
    dst     = os.path.join(AUDIO_DIR, fname)
    shutil.move(mp3_tmp, dst)
    print(f"[SERVER] Saved mp3 → {dst}")

    # 4) emit
    emit("bot_reply", {
        "advice": advice,
        "audio":  f"/static/audio/{fname}",
        "emotion": emotion
    })

if __name__ == "__main__":
    print("Therapist server running at http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
