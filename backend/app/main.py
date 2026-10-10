import time, json, asyncio
from fastapi import FastAPI, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import jwt
from . import core as c

app = FastAPI(title="Digital Me API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=c.S.ORIGINS, allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer(auto_error=False)

@app.middleware("http")
async def secure(request: Request, call_next):
    r = await call_next(request)
    r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer", "Cache-Control": "no-store"})
    return r

@app.on_event("startup")
def _start(): c.seed()

class Cred(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class Msg(BaseModel):
    text: str
    history: list[dict] = []

class Chunk(BaseModel):
    id: str
    text: str
    access: str = "public"
    tag: str = "general"

class Contact(BaseModel):
    name: str = Field(max_length=80)
    contact: str = Field(max_length=120)
    message: str = Field(min_length=3, max_length=1000)

def who(request: Request, cr: HTTPAuthorizationCredentials = Depends(bearer)):
    if not cr: return {"sub": f"guest:{request.client.host if request.client else 'x'}", "role": "visitor"}
    try: return c.read_token(cr.credentials)
    except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired token")

def owner(u=Depends(who)):
    if u["role"] != "owner": raise HTTPException(403, "Owner only")
    return u

async def chat_core(text, history, u):
    t0 = time.time(); trace = []
    history = [h for h in history if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str)][-6:]
    bad = c.check_input(u["sub"], text)
    if bad:
        c.audit(u["sub"], "blocked", bad); c.log_chat(u["sub"], text, bad, "neutral", True)
        return {"answer": bad, "emotion": "neutral", "blocked": True, "trace": ["guardrail: blocked"], "sources": [], "ms": 0}
    trace.append("guardrail: input clean")
    mood = c.emotion(text); trace.append(f"emotion: {mood}")
    ctx = c.retrieve(text, u["role"]); trace.append(f"vector search: {len(ctx)} chunks, top score {ctx[0]['score'] if ctx else 0}, role={u['role']}")
    try: ans = await c.agent(text, ctx, mood, history, trace)
    except Exception as e:
        ans = ctx[0]["text"] if ctx else "The language model is unavailable right now."; trace.append(f"llm fallback: {type(e).__name__}")
    ans = c.redact(ans, u["role"]); trace.append("output guard: PII redaction on" if u["role"] != "owner" else "output guard: owner, no redaction")
    c.log_chat(u["sub"], text, ans, mood, False)
    return {"answer": ans, "emotion": mood, "blocked": False, "trace": trace, "sources": [x["tag"] for x in ctx], "ms": int((time.time() - t0) * 1000)}

@app.get("/health")
def health(): return {"ok": True, "llm": bool(c.S.LLM_KEY), "chunks": c._col.count(), "voice": "custom" if __import__("os").getenv("VOICE_URL") else "edge-tts"}

@app.post("/auth/register")
def register(b: Cred):
    role = c.register(b.email, b.password)
    if not role: raise HTTPException(409, "Email already registered")
    c.audit(b.email, "register", role); return {"token": c.make_token(b.email, role), "role": role}

@app.post("/auth/login")
def login(b: Cred):
    role = c.login(b.email, b.password)
    if not role: c.audit(b.email, "login_failed"); raise HTTPException(401, "Wrong email or password")
    return {"token": c.make_token(b.email, role), "role": role}

@app.get("/me")
def me(u=Depends(who)): return {"email": u["sub"], "role": u["role"]}

@app.post("/chat")
async def chat(m: Msg, u=Depends(who)): return await chat_core(m.text, m.history, u)

@app.post("/chat/stream")
async def chat_stream(m: Msg, u=Depends(who)):
    r = await chat_core(m.text, m.history, u)
    async def gen():
        yield f"data: {json.dumps({'meta': {k: r[k] for k in ('emotion', 'blocked', 'trace', 'sources')}})}\n\n"
        words = r["answer"].split(" ")
        for i in range(0, len(words), 2):
            yield f"data: {json.dumps({'t': ' '.join(words[i:i+2]) + ' '})}\n\n"; await asyncio.sleep(.02)
        yield f"data: {json.dumps({'done': True, 'ms': r['ms']})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.websocket("/ws")
async def ws(sock: WebSocket, token: str = ""):
    await sock.accept()
    try: u = c.read_token(token) if token else {"sub": f"guest:{sock.client.host}", "role": "visitor"}
    except jwt.PyJWTError: await sock.close(4401); return
    hist = []
    try:
        while True:
            d = await sock.receive_json(); q = str(d.get("text", ""))[:800]
            r = await chat_core(q, hist, u); hist += [{"role": "user", "content": q}, {"role": "assistant", "content": r["answer"]}]; hist = hist[-8:]
            await sock.send_json(r)
    except WebSocketDisconnect: pass

@app.get("/tts")
async def tts(text: str, lang: str = "en", u=Depends(who)):
    text = text[:400]
    bad = c.check_input(u["sub"], text)
    if bad: raise HTTPException(429, bad)
    try: data, mime = await c.tts(text, lang)
    except Exception: raise HTTPException(503, "Voice service unavailable")
    return Response(data, media_type=mime)

@app.post("/contact")
def contact(b: Contact, u=Depends(who)):
    bad = c.check_input(u["sub"], b.message)
    if bad: raise HTTPException(429, bad)
    c.save_msg(b.name, b.contact, b.message); return {"ok": True}

@app.post("/ingest")
def ingest(ch: Chunk, u=Depends(owner)):
    c.add_chunk(ch.id, ch.text, ch.access if ch.access in ("public", "owner") else "owner", ch.tag); c.audit(u["sub"], "ingest", ch.id)
    return {"ok": True, "chunks": c._col.count()}

@app.get("/admin/stats")
def stats(u=Depends(owner)): return c.stats()

@app.get("/admin/messages")
def msgs(u=Depends(owner)): return c.messages()
