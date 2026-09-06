# -*- coding: utf-8 -*-
"""
AtriaTrade Web App v1.4
- Login-first secure dashboard (HMAC session cookie)
- Telemetry + Bot control endpoints
- 100% Paper-Trading safe
"""
from __future__ import annotations

import hmac
import hashlib
import os
import secrets
import time
from typing import Any, Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

try:
    from src.dashboard.server import DashboardServer
    from src.dashboard.auth import SecureAuthManager
except ImportError as e:
    print(f"❌ ImportError: Could not import dashboard components: {e}")
    raise

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
ADMIN_PIN = "402139235"
SERVER_SECRET = os.environ.get("ATRIA_SECRET") or secrets.token_hex(32)
SESSION_COOKIE = "atria_session"
SESSION_TTL = 12 * 3600  # 12 hours

LOGIN_RATE: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS, LOGIN_WINDOW = 5, 60

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(WEB_DIR, "templates"))
STATIC_DIR = os.path.join(WEB_DIR, "static")

auth_manager = SecureAuthManager()
dashboard_server = DashboardServer(auth_manager=auth_manager)

BOT_STATE = {
    "status": "RUNNING", "mode": "PAPER_TRADING", "autopilot": True,
    "btc_price": 95240.50, "total_equity": 10250.00, "reserve_usdt": 250.00,
    "win_rate": 78.5, "total_profit_usdt": 250.00, "rsi": 54.2, "trend": "BULLISH 📈",
    "position": {"side": "FLAT", "amount": 0, "entry_price": 0, "pnl": 0, "pnl_pct": 0, "tp": 0, "sl": 0},
    "recent_trades": [], "logs": ["[BOOT] AtriaTrade v1.4 online — Secure Mode ✅"],
}

# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------
app = FastAPI(title="AtriaTrade Dashboard API", version="1.4.0")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def add_log(msg: str):
    BOT_STATE["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(BOT_STATE["logs"]) > 80:
        BOT_STATE["logs"].pop(0)


# ---------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------
def _sign(payload: str) -> str:
    return hmac.new(SERVER_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session_token() -> str:
    exp = str(int(time.time()) + SESSION_TTL)
    return f"{exp}.{_sign(exp)}"


def is_valid_session(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    exp, sig = token.split(".", 1)
    if not hmac.compare_digest(sig, _sign(exp)):
        return False
    try:
        return int(exp) > time.time()
    except ValueError:
        return False


async def auth_gate(request: Request, call_next):
    """Login-first middleware for every route except auth endpoints."""
    path = request.url.path
    public = path in ("/login", "/api/auth/login") or path.startswith("/static")
    if not public and not is_valid_session(request.cookies.get(SESSION_COOKIE)):
        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"success": False, "error": "Not authenticated"})
        return RedirectResponse("/login", status_code=302)
    return await call_next(request)

app.middleware("http")(auth_gate)


# ---------------------------------------------------------------------
# Login UI (self-contained, cyberpunk)
# ---------------------------------------------------------------------
LOGIN_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ورود | AtriaTrade</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#05070d;font-family:Vazirmatn,Tahoma,sans-serif}
.grid-bg{background-image:linear-gradient(rgba(0,255,170,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,170,.06) 1px,transparent 1px);background-size:32px 32px}
.glow{box-shadow:0 0 24px rgba(0,255,170,.25)}</style></head>
<body class="grid-bg min-h-screen flex items-center justify-center">
<div class="bg-[#0b101c] border border-emerald-500/30 rounded-2xl p-8 w-80 glow text-center">
  <div class="text-5xl mb-3">🛡️</div>
  <h1 class="text-emerald-400 font-bold text-xl mb-1 tracking-wider">ATRIATRADE</h1>
  <p class="text-gray-500 text-sm mb-6">ورود امن به مرکز کنترل</p>
  <input id="pin" type="password" inputmode="numeric" maxlength="12" placeholder="PIN ورود"
    class="w-full bg-black/40 border border-emerald-500/30 rounded-lg px-4 py-3 text-center text-emerald-300 tracking-widest text-lg outline-none focus:border-emerald-400 mb-3">
  <button onclick="doLogin()" class="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold py-3 rounded-lg transition">🔓 ورود</button>
  <p id="err" class="text-red-400 text-sm mt-3 h-5"></p>
</div>
<script>
async function doLogin(){
  const r = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:document.getElementById('pin').value})});
  if(r.ok){location.href='/';}else{document.getElementById('err').textContent=(await r.json()).error||'PIN نامعتبر';}
}
document.getElementById('pin').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
</script></body></html>"""


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(LOGIN_HTML)


@app.post("/api/auth/login")
async def login(request: Request, payload: Dict[str, Any] = None):
    body = await request.json()
    ip = request.client.host if request.client else "?"
    now = time.time()
    attempts = [t for t in LOGIN_RATE.get(ip, []) if now - t < LOGIN_WINDOW]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    if body.get("pin") != ADMIN_PIN:
        attempts.append(now)
        LOGIN_RATE[ip] = attempts
        raise HTTPException(status_code=401, detail="PIN نامعتبر است.")
    LOGIN_RATE.pop(ip, None)
    add_log("🔓 Admin login successful.")
    resp = JSONResponse(content={"success": True})
    resp.set_cookie(SESSION_COOKIE, make_session_token(), httponly=True, samesite="lax", max_age=SESSION_TTL)
    return resp


@app.post("/api/auth/logout")
async def logout():
    add_log("🔒 Admin logged out.")
    resp = JSONResponse(content={"success": True})
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page_title": "AtriaTrade Dashboard Pro"})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page_title": "AtriaTrade Dashboard Pro"})


# ---------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------
@app.get("/api/telemetry")
async def telemetry():
    import random
    BOT_STATE["btc_price"] = round(BOT_STATE["btc_price"] + random.uniform(-15, 15), 2)
    pos = BOT_STATE["position"]
    if pos.get("side") != "FLAT":
        sign = 1 if pos["side"] == "LONG" else -1
        pnl = round((BOT_STATE["btc_price"] - pos["entry_price"]) * pos["amount"] * sign, 2)
        pos["pnl"] = pnl
        pos["pnl_pct"] = round(pnl / (pos["entry_price"] * pos["amount"]) * 100, 2)
    return JSONResponse(content={
        "status": BOT_STATE["status"], "mode": BOT_STATE["mode"], "autopilot": BOT_STATE["autopilot"],
        "btc_price": BOT_STATE["btc_price"], "current_price": BOT_STATE["btc_price"],
        "price_str": f"{BOT_STATE['btc_price']:,.2f}",
        "total_equity": round(BOT_STATE["total_equity"] + pos.get("pnl", 0), 2), "equity": BOT_STATE["total_equity"],
        "reserve_usdt": BOT_STATE["reserve_usdt"], "safe_profit": BOT_STATE["reserve_usdt"],
        "win_rate": BOT_STATE["win_rate"], "total_profit_usdt": BOT_STATE["total_profit_usdt"],
        "rsi": BOT_STATE["rsi"], "trend": BOT_STATE["trend"],
        "position": pos, "active_position": pos,
        "recent_trades": BOT_STATE["recent_trades"], "logs": BOT_STATE["logs"],
        "timestamp": time.time(),
    })


# ---------------------------------------------------------------------
# Bot actions
# ---------------------------------------------------------------------
def open_position(side: str, amount: float):
    p = BOT_STATE["btc_price"]
    BOT_STATE["position"] = {
        "side": side, "amount": amount, "entry_price": p, "pnl": 0.0, "pnl_pct": 0.0,
        "tp": round(p * (1.02 if side == "LONG" else 0.98), 2),
        "sl": round(p * (0.98 if side == "LONG" else 1.02), 2),
    }
    add_log(f"{'🟢' if side == 'LONG' else '🔴'} Manual {side}: {amount} BTC @ ${p:,.2f}")


@app.post("/api/action")
async def action(payload: Dict[str, Any] = None):
    raw = dict(payload or {})
    act = str(raw.get("action", "")).upper()
    amount = float(raw.get("amount", 0.02))

    if act in ("BUY", "LONG"):
        open_position("LONG", amount)
        return {"success": True, "message": f"LONG {amount} BTC (Paper)"}
    if act in ("SELL", "SHORT"):
        open_position("SHORT", amount)
        return {"success": True, "message": f"SHORT {amount} BTC (Paper)"}
    if act in ("CLOSE", "CLOSE_POSITION"):
        pos = BOT_STATE["position"]
        if pos.get("side") == "FLAT":
            return {"success": False, "message": "No active position"}
        pnl = pos.get("pnl", 0.0)
        BOT_STATE["total_equity"] += pnl
        BOT_STATE["total_profit_usdt"] += pnl
        BOT_STATE["recent_trades"].insert(0, {"time": time.strftime("%H:%M:%S"), "time_str": time.strftime("%H:%M:%S"),
                                              "action": "CLOSE", "side": pos["side"], "amount": pos["amount"],
                                              "entry_price": pos["entry_price"], "exit_price": BOT_STATE["btc_price"], "pnl": pnl})
        BOT_STATE["recent_trades"] = BOT_STATE["recent_trades"][:10]
        add_log(f"⚪ Closed {pos['side']} | Realized PnL: ${pnl:+.2f}")
        BOT_STATE["position"] = {"side": "FLAT", "amount": 0, "entry_price": 0, "pnl": 0, "pnl_pct": 0, "tp": 0, "sl": 0}
        return {"success": True, "message": f"Closed with PnL ${pnl:+.2f}"}
    if act in ("START", "RESUME"):
        BOT_STATE["status"] = "RUNNING"; add_log("▶ Engine resumed.")
        return {"success": True, "status": "RUNNING"}
    if act in ("STOP", "PAUSE"):
        BOT_STATE["status"] = "PAUSED"; add_log("⏸ Engine paused.")
        return {"success": True, "status": "PAUSED"}
    if act == "TOGGLE_AUTOPILOT":
        BOT_STATE["autopilot"] = not BOT_STATE["autopilot"]
        add_log(f"🤖 Auto-Pilot {'ENABLED' if BOT_STATE['autopilot'] else 'DISABLED'}.")
        return {"success": True, "autopilot": BOT_STATE["autopilot"]}
    return {"success": False, "message": f"Unknown action: {act}"}


@app.post("/api/order/close")
async def close_order():
    return await action({"action": "CLOSE"})


@app.post("/api/panic")
async def panic():
    add_log("🚨 PANIC! Closing all positions & stopping engine.")
    await action({"action": "CLOSE"})
    BOT_STATE["status"] = "STOPPED"
    BOT_STATE["autopilot"] = False
    return {"success": True, "message": "Panic executed."}


# ---------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 AtriaTrade v1.4 — Secure Dashboard (Login Required)")
    print("   http://127.0.0.1:8080")
    print("=" * 60 + "\n")
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8080, reload=False)
