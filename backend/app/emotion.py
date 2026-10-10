"""Webcam emotion: OpenCV face detection + FER+ CNN (ONNX). Frames are processed in memory and never stored."""
import os
from pathlib import Path
import numpy as np, cv2

MODEL = Path(os.getenv("EMOTION_MODEL", "/models/emotion-ferplus-8.onnx"))
LABELS = ["neutral", "joy", "surprise", "sad", "angry", "disgust", "fear", "contempt"]   # FER+ output order
MOOD = {"joy": "joy", "surprise": "surprise", "sad": "sad", "angry": "angry"}
_sess = _cas = None

def _load():
    global _sess, _cas
    if _sess is None:
        import onnxruntime as ort
        _sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
        _cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def classify(jpeg: bytes):
    _load()
    img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None: raise ValueError("bad image")
    faces = _cas.detectMultiScale(img, 1.2, 5, minSize=(60, 60))
    if len(faces) == 0: return {"face": False, "emotion": "neutral", "mood": "neutral", "confidence": 0.0}
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    crop = cv2.resize(img[y:y + h, x:x + w], (64, 64)).astype(np.float32)[None, None]
    out = _sess.run(None, {_sess.get_inputs()[0].name: crop})[0][0]
    e = np.exp(out - out.max()); p = e / e.sum(); i = int(p.argmax())
    return {"face": True, "emotion": LABELS[i], "mood": MOOD.get(LABELS[i], "neutral"), "confidence": round(float(p[i]), 3)}
