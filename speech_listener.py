import speech_recognition as sr

def listen_to_user():
    recognizer = sr.Recognizer()
    # if you like, bump up for a noisy room
    recognizer.energy_threshold = 100  
    # this is the key: after 3 seconds of silence, listen() returns
    recognizer.pause_threshold = 3.0

    with sr.Microphone() as source:
        # optional: calibrate to ambient noise for 1 second
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("🎤 Speak now (will auto-stop after 3 s of silence)…")
        audio = recognizer.listen(source)  

    try:
        text = recognizer.recognize_google(audio)
        print("🗣️ You said:", text)
        return text
    except sr.UnknownValueError:
        print("🤷‍♂️ Couldn't understand audio")
    except sr.RequestError as e:
        print(f"🚫 Speech recognition error: {e}")
    return None

if __name__ == "__main__":
    listen_to_user()
