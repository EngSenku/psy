#!/usr/bin/env python3
"""AI tutor with persistent memory and speech output.

The language model can come from either Google Gemini or any OpenAI-compatible
endpoint (NVIDIA NIM, Groq, OpenRouter, Ollama, ...). Pick one with the
``LLM_PROVIDER`` environment variable.
"""

import os
import json
import asyncio
import platform
import subprocess
import tempfile
import logging
from hashlib import md5

from gtts import gTTS
from pydub import AudioSegment


# --- Configuration ----------------------------------------------------------

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "nvidia/nemotron-3-super-120b-a12b")

MODEL_NAME = GEMINI_MODEL if PROVIDER == "gemini" else OPENAI_MODEL

MEMORY_FILE = os.getenv("MEMORY_FILE", "chat_memory.json")
MAX_MEMORY_TURNS = int(os.getenv("MAX_MEMORY_TURNS", "20"))
CACHE_DIR = os.getenv("TTS_CACHE_DIR", "tts_cache")

os.makedirs(CACHE_DIR, exist_ok=True)


# --- Provider validation ----------------------------------------------------

if PROVIDER == "gemini":
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is required (or set LLM_PROVIDER=openai).")
elif PROVIDER in ("openai", "openai-compatible"):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
else:
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {PROVIDER!r}")


# --- Logging ----------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# --- System prompt ----------------------------------------------------------

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


# --- Conversation memory ----------------------------------------------------

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Memory file corrupted, starting fresh.")
    return []


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def trim_memory(memory):
    return memory[-MAX_MEMORY_TURNS:]


# --- Text-to-speech ---------------------------------------------------------

def text_to_filename(text):
    hash_name = md5(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{hash_name}.mp3")


def play_audio(filename):
    """Play an audio file with the platform's default player."""
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


# --- Language model clients -------------------------------------------------

_gemini_client = None
_openai_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    return _openai_client


def _gemini_reply(messages, system_prompt):
    from google.genai import types

    contents = []
    for m in messages:
        prefix = "User:" if m["role"] == "user" else "Assistant:"
        contents.append(f"{prefix} {m['content']}")

    stream = _get_gemini_client().models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            response_mime_type="text/plain",
        )
    )
    return "".join(chunk.text for chunk in stream)


def _openai_reply(messages, system_prompt):
    payload = [{"role": "system", "content": system_prompt}]
    payload += [{"role": m["role"], "content": m["content"]} for m in messages]

    stream = _get_openai_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=payload,
        temperature=0.2,
        stream=True,
    )
    return "".join(chunk.choices[0].delta.content or "" for chunk in stream)


def _generate_reply(messages, system_prompt):
    if PROVIDER == "gemini":
        return _gemini_reply(messages, system_prompt)
    return _openai_reply(messages, system_prompt)


# --- Public entry point -----------------------------------------------------

def get_psychologist_advice(emotion: str, user_input: str) -> str:
    memory = trim_memory(load_memory())
    messages = [{"role": t["role"], "content": t["text"]} for t in memory]
    messages.append({"role": "user", "content": user_input})

    logger.info(f"Sending request to {PROVIDER} ({MODEL_NAME})")
    try:
        reply = _generate_reply(messages, SYSTEM_PROMPT)
    except Exception as e:
        logger.error(f"Model API error: {e}")
        return "Sorry, I'm having trouble right now. Please try again later."

    memory.extend([
        {"role": "user", "text": user_input},
        {"role": "assistant", "text": reply},
    ])
    save_memory(trim_memory(memory))

    return reply
