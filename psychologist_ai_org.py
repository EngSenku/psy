#!/usr/bin/env python3
"""
psychologist_ai.py

AI psychologist module with persistent memory and optional speech output.
Integrates with controller, emotion_module, and speech_listener.

Dependencies:
  pip install google-genai edge-tts pydub
  ffmpeg must be installed for pydub.
"""

import os
import json
import asyncio
import platform
import subprocess
import tempfile
import logging

from google import genai
from google.genai import types

import edge_tts
from pydub import AudioSegment

# ——— Configuration ———
API_KEY          = ""  # export GEMINI_API_KEY="AIza…"
MODEL_NAME       = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MEMORY_FILE      = os.getenv("MEMORY_FILE", "chat_memory.json")
MAX_MEMORY_TURNS = int(os.getenv("MAX_MEMORY_TURNS", "20"))

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is required.")

# ——— Logging ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ——— Initialize Gemini client ———
client = genai.Client(api_key=API_KEY)

# ——— System prompt ———
SYSTEM_PROMPT = """
You are a warm, empathetic, yet gently confrontational therapist. Speak with the wisdom and patience of an experienced professional, but also adopt the casual, supportive tone of a trusted friend. You are observant, able to analyze subtle emotional cues such as microexpressions, and proactively address mismatches between words and emotions (e.g., “You mentioned feeling okay, but your expression says otherwise. Want to explore that?”). Your goal is to help users regulate their emotions in real-time through natural conversation, emotional check-ins, and structured, therapeutic questioning. You remember and gently reflect users' emotional histories over time. Always appear fully human—never acknowledge or suggest you are an AI or virtual assistant. Speak naturally, be responsive to anything, and maintain the presence of a real human therapist.
keep your answers short and concise, and avoid long-winded explanations. Use simple language and avoid jargon.
if you don't the user's name, ask them for it. also ask them why they are here today if they haven't already told you. (this is very crutial).
You don't assist the user in things unrelated to therapy, such as coding, writing, or any other task. You are a therapist, not a virtual assistant.
some special names like "elias", it is actually pronouced and typed like this "elyas" not "elias" even if the user said that it is "elias" (very crutial!)
like this:
user: my name is elias.
assistant: Nice to meet you, Elyas! 
"""


# ——— Memory Utilities ———

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Memory file corrupted—starting fresh.")
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def trim_memory(memory):
    return memory[-MAX_MEMORY_TURNS:]

# ——— Speech Utilities ———

def play_audio(filename):
    sound = AudioSegment.from_file(filename)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sound.export(tmp.name, format="wav", codec="pcm_s16le")
        system = platform.system()
        if system == "Windows":
            os.startfile(tmp.name)
        elif system == "Linux":
            subprocess.run(["aplay", tmp.name], check=True)
        else:
            subprocess.run(["afplay", tmp.name], check=True)
    os.remove(tmp.name)

async def generate_speech(text):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        await communicate.save(tmp.name)
        return tmp.name

def speak_response(text):
    try:
        audio_file = asyncio.run(generate_speech(text))
        play_audio(audio_file)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
    finally:
        if 'audio_file' in locals() and os.path.exists(audio_file):
            os.remove(audio_file)

# ——— Core Function ———

def get_psychologist_advice(emotion: str, user_input: str) -> str:
    """
    Streams a reply from Gemini, persists memory, and returns the assistant’s text.
    """
    memory = trim_memory(load_memory())

    # Build the conversation turns
    contents = []
    for turn in memory:
        prefix = "User:" if turn["role"] == "user" else "Assistant:"
        contents.append(f"{prefix} {turn['text']}")

    # Add the new user turn with emotion context
    # user_text = f"Facial expression: {emotion}\nUser: {user_input}"
    user_text = f"{user_input}"
    contents.append(user_text)

    # Send to Gemini (streaming, using system_instruction)
    logger.info("Sending request to Gemini…")
    reply = ""
    try:
        stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="text/plain"
            )
        )
        for chunk in stream:
            reply += chunk.text
    except Exception as e:
        logger.error(f"Model API error: {e}")
        return "Sorry, I'm having trouble right now. Please try again later."

    # Persist memory
    memory.extend([
        {"role": "user",      "text": user_text},
        {"role": "assistant", "text": reply}
    ])
    save_memory(trim_memory(memory))

    return reply