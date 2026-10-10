"""Multi-agent LangGraph: router -> (knowledge | tools | contact) -> critic (fact-check loop)."""
import re
from typing import TypedDict
from . import core as c
try:
    from langgraph.graph import StateGraph, END
    AVAILABLE = True
except Exception:
    AVAILABLE = False

class St(TypedDict, total=False):
    q: str; mood: str; hist: list; ctx: list; route: str; draft: str; verdict: str; tries: int; trace: list

async def router(s):
    q = s["q"]
    if re.search(r"github|repos?\b|repositor|\btime\b|today'?s date", q, re.I): r = "tools"
    elif re.search(r"leave a message|contact|hire|reach him|get in touch|message for", q, re.I): r = "contact"
    else: r = "knowledge"
    s["trace"].append(f"graph router: {r} agent"); return {"route": r}

async def knowledge(s):
    d = await c.answer_from_context(s["q"], s["ctx"], s["mood"], s["hist"])
    s["trace"].append(f"graph knowledge agent: draft {s.get('tries', 0) + 1}"); return {"draft": d, "tries": s.get("tries", 0) + 1}

async def tools(s):
    d = await c.agent(s["q"], s["ctx"], s["mood"], s["hist"], s["trace"]); s["trace"].append("graph tool agent: done"); return {"draft": d}

async def contact(s):
    if not c.S.LLM_KEY:
        return {"draft": "I can pass a message to Nikhil. Use the contact form on this page, or tell me your name, how to reach you, and your message."}
    q = "If the visitor gave a message and contact details, save them with leave_message. Otherwise ask for their name, contact and message.\nVisitor: " + s["q"]
    d = await c.agent(q, s["ctx"], s["mood"], s["hist"], s["trace"]); s["trace"].append("graph contact agent: done"); return {"draft": d}

async def critic(s):
    if not c.S.LLM_KEY or s["route"] != "knowledge" or not s["ctx"]:
        s["trace"].append("graph critic: skipped"); return {"verdict": "ok"}
    block = "\n".join(x["text"] for x in s["ctx"])
    v = await c.complete([{"role": "system", "content": "You are a strict fact checker. Reply with exactly OK if every claim in ANSWER is supported by CONTEXT, otherwise REWRITE."},
                          {"role": "user", "content": f"CONTEXT:\n{block}\n\nANSWER:\n{s['draft']}"}], 0, 5)
    ok = v.strip().upper().startswith("OK"); s["trace"].append(f"graph critic: {'approved' if ok else 'asked for rewrite'}")
    return {"verdict": "ok" if ok else "rewrite"}

_app = None
def _build():
    g = StateGraph(St)
    for n, f in (("router", router), ("knowledge", knowledge), ("tools", tools), ("contact", contact), ("critic", critic)): g.add_node(n, f)
    g.set_entry_point("router")
    g.add_conditional_edges("router", lambda s: s["route"], {"knowledge": "knowledge", "tools": "tools", "contact": "contact"})
    g.add_edge("knowledge", "critic"); g.add_edge("tools", END); g.add_edge("contact", END)
    g.add_conditional_edges("critic", lambda s: "knowledge" if s.get("verdict") == "rewrite" and s.get("tries", 0) < 2 else "end", {"knowledge": "knowledge", "end": END})
    return g.compile()

async def run(q, ctx, mood, hist, trace):
    global _app
    _app = _app or _build()
    out = await _app.ainvoke({"q": q, "ctx": ctx, "mood": mood, "hist": hist, "trace": trace, "tries": 0})
    return out["draft"]
