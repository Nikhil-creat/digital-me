"""Cloned-voice service (Coqui XTTS v2). Clone ONLY your own voice, from a clean 10-30 s sample at sample/me.wav."""
import os, tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

SAMPLE = os.getenv("SPEAKER_WAV", "/app/sample/me.wav")
app = FastAPI(); _tts = None

class Req(BaseModel):
    text: str
    language: str = "en"

@app.get("/health")
def health(): return {"ok": True, "sample": os.path.exists(SAMPLE)}

@app.post("/tts")
def synth(r: Req):
    global _tts
    if not os.path.exists(SAMPLE): raise HTTPException(503, "Put your own voice recording at services/voice/sample/me.wav")
    if r.language not in ("en", "hi"): raise HTTPException(422, "XTTS here supports en and hi; the API falls back to the standard voice")
    if _tts is None:
        import torch; from TTS.api import TTS
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda" if torch.cuda.is_available() else "cpu")
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        _tts.tts_to_file(text=r.text[:400], speaker_wav=SAMPLE, language=r.language, file_path=f.name)
        return Response(open(f.name, "rb").read(), media_type="audio/wav")
