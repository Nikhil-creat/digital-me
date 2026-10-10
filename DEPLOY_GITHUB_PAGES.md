# Deploy to GitHub Pages (step by step)

GitHub Pages hosts only the **frontend** (`docs/`). The backend (`backend/`) runs on a server you choose; the site works in demo mode without it.

## A. Publish the site (10 minutes, phone or PC)
1. Create a **public** repo on github.com, e.g. `digital-me` (no README).
2. Create a **Personal Access Token**: GitHub → Settings → Developer settings → Tokens (classic) → scopes **repo** AND **workflow** (the workflow scope is required because this project contains `.github/workflows`).
3. Push the project (PC terminal or Termux):
```
unzip digital-me-master.zip && cd digital-me
git init && git branch -M main
git add . && git commit -m "Digital Me v3"
git remote add origin https://github.com/Nikhil-creat/digital-me.git
git push -u origin main        # username: Nikhil-creat, password: your token
```
4. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. Repo → **Actions** tab → wait for "Deploy site" to turn green (1-2 minutes).
6. Open `https://nikhil-creat.github.io/digital-me/`. Install it from the browser menu ("Add to Home screen").

No Actions? Delete `.github/workflows/pages.yml`, then Pages → Source: **Deploy from a branch** → `main` / `/docs`.

## B. Go live with the backend
1. Get a small server (any VPS with Docker; Oracle Cloud free tier, Hetzner, DigitalOcean, or Render/Railway/Fly.io).
2. Point a domain (or subdomain like `api.yourdomain.com`) A-record at the server.
3. On the server: `git clone` your repo → `cd backend && cp .env.example .env` and set:
   `JWT_SECRET` (run `openssl rand -hex 32`), `OWNER_EMAIL`, `LLM_API_KEY` (free Groq key), `DOMAIN`, `CORS_ORIGINS=https://nikhil-creat.github.io`
4. `docker compose up -d --build` → Caddy issues the HTTPS certificate automatically. Check `https://api.yourdomain.com/health`.
5. Open your Pages site → paste the API URL into **Backend → Connect** (or set it in `docs/config.js` and push again).
6. **Register** with your `OWNER_EMAIL` → you are the owner. Add private notes in the Owner dashboard.

## C. Optional upgrades (see services/README.md)
- Cloned voice: `docker compose --profile voice up -d --build`
- Photoreal talking avatar: `docker compose --profile avatar up -d --build` (GPU recommended)
- Camera mood: just click **Camera mood** on the page (needs the backend, works on CPU).

## Troubleshooting
- Push rejected, "refusing to allow ... workflow": your token lacks the `workflow` scope.
- Page shows "demo mode": API URL empty or unreachable. It must be `https://`.
- CORS error in the browser console: `CORS_ORIGINS` must exactly match your Pages origin, with no trailing slash.
- Mic or camera does nothing: both need HTTPS and a permission tap.
