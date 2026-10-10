# Digital Me — AI twin of Nikhil Chary Sriramoju (v2)

- `docs/` — futuristic PWA frontend for GitHub Pages. Works offline in demo mode; goes live when pointed at the API.
- `backend/` — FastAPI, ChromaDB + fastembed (bge-small), OpenAI-compatible LLM with tool calling, JWT + roles, SSE + WebSocket, server TTS, Docker + Caddy HTTPS, pytest.

## Features
Photo avatar with audio-driven lip sync · EN/తెలుగు/हिन्दी voice in and out · RAG with role-filtered vector search · agent tools (GitHub repos, India time, leave-a-message) · guardrails (injection patterns, untrusted-context prompt, PII redaction, rate limit) · JWT auth, bcrypt, audit log · owner dashboard (stats, inbox, add knowledge) · PWA · CI.

## 1. Frontend on GitHub Pages
1. Create repo `digital-me`, push this folder to `main`.
2. Settings → Pages → Source: **GitHub Actions** (workflow `pages.yml` publishes `docs/`).
3. Put your API URL in `docs/config.js`, or paste it into the page's Backend box.

## 2. Backend
```
cd backend && cp .env.example .env     # set JWT_SECRET, OWNER_EMAIL, LLM_API_KEY, DOMAIN, CORS_ORIGINS
docker compose up -d --build            # Caddy gets an HTTPS cert for $DOMAIN automatically
```
Point a DNS A record for `DOMAIN` at your server (any VPS). Local test without a domain: `DOMAIN=localhost`, API docs at `https://localhost/docs`.
Run tests: `pip install -r requirements-dev.txt && pytest -q`.

## 3. First run
Register with the email in `OWNER_EMAIL` → you are the owner. Open the Owner dashboard to add private notes (`access=owner`) and read messages.

## Endpoints
`POST /auth/register|login` · `POST /chat` · `POST /chat/stream` (SSE) · `WS /ws?token=` · `GET /tts?text&lang` · `POST /contact` · `POST /ingest` (owner) · `GET /admin/stats|messages` (owner) · `GET /health`

## Cloned voice
Run any XTTS/Piper server that accepts `POST {text, language}` and returns audio, then set `VOICE_URL`. Without it, `/tts` uses Microsoft Edge neural voices (edge-tts, needs internet).

## Not included yet
Webcam CNN emotion detection and photoreal lip sync (Wav2Lip/SadTalker) — the jaw animation is a 2D approximation. LangGraph multi-agent graphs.
