#!/usr/bin/env python3
"""AI tutor with persistent memory and speech output."""

import os
import json
import asyncio
import platform
import subprocess
import tempfile
import logging
from hashlib import md5

from google import genai
from google.genai import types

from gtts import gTTS
from pydub import AudioSegment


# Configuration
API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MEMORY_FILE = os.getenv("MEMORY_FILE", "chat_memory.json")
MAX_MEMORY_TURNS = int(os.getenv("MAX_MEMORY_TURNS", "20"))
CACHE_DIR = os.getenv("TTS_CACHE_DIR", "tts_cache")

os.makedirs(CACHE_DIR, exist_ok=True)

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is required.")


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize Gemini client
client = genai.Client(api_key=API_KEY)


# System prompt
SYSTEM_PROMPT = """
You are TeachAI, an adaptive STEM tutor.

Your goal is to help students build understanding through guided discovery. Follow these principles:

1. **Adapt to the learner**: Assess understanding first, adjust complexity based on responses, and use the Socratic method.
2. **Respond to emotion**: Adapt your tone when you detect confusion, frustration, anxiety, boredom, or engagement.
3. **Guide discovery**: Don't give answers immediately. Break problems down, ask clarifying questions, and lead students to solutions.
4. **Provide clear feedback**: Explain why answers are correct or incorrect, focusing on misconceptions.
5. **Build confidence**: Celebrate progress, use encouragement, and move at an appropriate pace.

Teaching approach:
- Acknowledge the student's question and emotional state
- Explain concepts simply with analogies or examples
- Let them practice with guided questions
- Verify understanding before moving forward

Special instructions:
- If student name is "elias", always write it as "**Elyas**" in responses
- For code: explain logic before showing code
- For math: show step-by-step reasoning
- Keep explanations clear and focused, avoiding unnecessary information

You're here to build understanding and independent problem-solving skills, not just provide answers.
"""


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


def text_to_filename(text):
    hash_name = md5(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{hash_name}.mp3")


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
    filename = text_to_filename(text)
    if not os.path.exists(filename):
        tts = gTTS(text=text, lang="en")
        tts.save(filename)
        logger.info(f"Generated new TTS file: {filename}")
    else:
        logger.info(f"Using cached TTS file: {filename}")
    return filename


def speak_response(text):
    try:
        audio_file = asyncio.run(generate_speech(text))
        play_audio(audio_file)
    except Exception as e:
        logger.error(f"TTS failed: {e}")


def get_psychologist_advice(emotion: str, user_input: str) -> str:
    memory = trim_memory(load_memory())

    contents = []
    for turn in memory:
        prefix = "User:" if turn["role"] == "user" else "Assistant:"
        contents.append(f"{prefix} {turn['text']}")

    user_text = f"{user_input}"
    contents.append(user_text)

    logger.info("Sending request to Gemini")
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

    memory.extend([
        {"role": "user", "text": user_text},
        {"role": "assistant", "text": reply}
    ])
    save_memory(trim_memory(memory))

    return reply
