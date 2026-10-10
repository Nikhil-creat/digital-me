# Optional services

## voice/ — your cloned voice (XTTS v2)
1. Record 10-30 s of your own clean voice, save as `voice/sample/me.wav`. Clone only your own voice.
2. Read the Coqui model license (non-commercial), then set `COQUI_TOS_AGREED=1` in `backend/.env`.
3. In `backend/.env`: `VOICE_URL=http://voice:8020/tts`, then `docker compose --profile voice up -d --build`.
English and Hindi use your cloned voice. Telugu falls back to the standard voice automatically. First request downloads ~2 GB of models.

## lipsync/ — photoreal talking video (Wav2Lip)
1. Download `wav2lip_gan.pth` from the Wav2Lip repo's model links and put it in `lipsync/checkpoints/`.
2. `LIPSYNC_URL=http://lipsync:8030/render` in `backend/.env`, then `docker compose --profile avatar up -d --build`.
3. In the page, turn on "HD avatar". Each reply renders a video, so it needs a GPU to feel responsive.
Wav2Lip is research code with a non-commercial license. If the Docker build fails on library versions, adjust the pip line in `lipsync/Dockerfile`.
