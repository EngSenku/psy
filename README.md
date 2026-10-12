# AI Tutor - Emotion-Aware STEM Learning Assistant

An interactive AI-powered tutoring system that combines speech recognition, real-time emotion detection, and an animated 3D avatar to provide personalized STEM education.

## Features

- **Voice Interaction**: Natural speech input and output for hands-free learning
- **Emotion Detection**: Real-time facial emotion analysis to adapt teaching style
- **Adaptive Teaching**: Socratic approach that guides discovery rather than giving answers
- **3D Avatar**: Live2D animated character with lip-syncing during speech
- **Persistent Memory**: Maintains conversation history across sessions
- **Real-time Conversation**: WebSocket-based communication for responsive interaction
- **Cross-platform Audio**: Text-to-speech with local caching

## How It Works

1. **User speaks**: Speech recognition captures user input
2. **Emotion analysis**: Webcam captures facial expression, DeepFace analyzes emotions
3. **AI response**: Gemini generates adaptive tutoring response based on emotion and context
4. **Speech synthesis**: gTTS converts response to audio with caching
5. **Avatar animation**: Live2D model lip-syncs with the generated audio

## Tech Stack

- **Backend**: Flask, Flask-SocketIO, Eventlet
- **Frontend**: HTML5, JavaScript, PixiJS, Live2D Cubism
- **AI**: Google Gemini API
- **Computer Vision**: OpenCV, DeepFace
- **Speech**: SpeechRecognition (browser), gTTS (server)
- **Audio**: pydub

## Prerequisites

- Python 3.10 or 3.11
- FFmpeg installed for audio processing
- Webcam access
- Microphone access
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd psy
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export GEMINI_API_KEY="your_api_key_here"
export GEMINI_MODEL="gemini-2.5-flash"  # Optional
```

## Usage

1. Start the server:
```bash
python controller.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Allow microphone and camera permissions when prompted
4. Start speaking - the AI tutor will respond and adapt based on your emotions

## Project Structure

```
psy/
├── controller.py      # Flask server and WebSocket handling
├── psychologist_ai.py # AI logic and memory management
├── emotion_module.py  # Emotion detection using DeepFace
├── index.html         # Frontend interface
├── requirements.txt   # Python dependencies
├── haru/             # Live2D avatar model files
├── static/           # Static assets (images, audio)
├── tts_cache/        # Cached TTS audio files
└── ai/               # Chat memory storage
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | - | Google Gemini API key (required) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `MEMORY_FILE` | `chat_memory.json` | Path to memory file |
| `MAX_MEMORY_TURNS` | `20` | Maximum conversation turns to remember |
| `TTS_CACHE_DIR` | `tts_cache` | Directory for cached TTS files |

## Notes

- Emotion detection works best in good lighting with a clear view of the face
- Speech recognition requires an internet connection (browser-based)
- The first TTS generation may take a moment, but subsequent ones are cached
- Clear cached files periodically if disk space is a concern

## License

This project is open source and available for educational purposes.
