# emotion_module.py
import cv2
import base64
import numpy as np
from deepface import DeepFace

def analyze_emotion(img_b64: str) -> str:
    """Decode a base64 JPEG, run DeepFace emotion detection, return dominant if ≥50%."""
    if not img_b64:
        return "neutral"
    try:
        header, encoded = img_b64.split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = DeepFace.analyze(
            img_rgb,
            actions=["emotion"],
            detector_backend="mtcnn",
            enforce_detection=False
        )
        scores = res[0]["emotion"]
        if max(scores.values()) >= 50:
            return res[0]["dominant_emotion"]
    except Exception as e:
        print("❌ Emotion detection error:", e)
    return "neutral"
