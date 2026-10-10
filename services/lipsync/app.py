"""Photoreal lip-sync service wrapping Wav2Lip. POST /render (audio file) -> mp4 of your avatar speaking it."""
import os, shutil, subprocess, tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

FACE = os.getenv("FACE_IMG", "/app/assets/avatar.jpg")
CKPT = os.getenv("CKPT", "/app/Wav2Lip/checkpoints/wav2lip_gan.pth")
app = FastAPI()

@app.get("/health")
def health(): return {"ok": True, "checkpoint": os.path.exists(CKPT), "face": os.path.exists(FACE)}

@app.post("/render")
async def render(audio: UploadFile = File(...)):
    if not os.path.exists(CKPT): raise HTTPException(503, "Missing checkpoints/wav2lip_gan.pth (see README)")
    d = tempfile.mkdtemp()
    try:
        src, wav, out = f"{d}/in", f"{d}/a.wav", f"{d}/out.mp4"
        open(src, "wb").write(await audio.read())
        subprocess.run(["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", wav], check=True, capture_output=True)
        subprocess.run(["python", "inference.py", "--checkpoint_path", CKPT, "--face", FACE, "--audio", wav, "--outfile", out],
                       cwd="/app/Wav2Lip", check=True, capture_output=True, timeout=600)
        return Response(open(out, "rb").read(), media_type="video/mp4")
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, (e.stderr or b"")[-300:].decode(errors="ignore"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
