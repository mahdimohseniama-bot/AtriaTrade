import uvicorn, threading, time, random, os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="AtriaTrade Pro Dashboard API", version="1.4.0")
templates = Jinja2Templates(directory="src/web/templates")

# ================= STATE =================
class S:
    btc_price = 95400.00
    total_equity = 10000.00
    reserve_usdt = 2500.00
    win_rate = 68.4
    total_profit_usdt = 0.00
    rsi = 58.4
    trend = "BULLISH"
    autopilot = False
    position = None
    recent_trades = []
    logs = [f"[{time.strftime('%H:%M:%S')}] AtriaTrade Engine v1.4 Started"]

def log(msg: str):
    S.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    S.logs = S.logs[-60:]

def open_position(side: str, amount: float, source: str = "AUTO"):
    S.position = {
        "side": side,
        "amount": amount,
        "entry_price": S.btc_price,
        "pnl": 0.0,
        "tp": round(S.btc_price * (1.015 if side == "LONG" else 0.985), 2),
        "sl": round(S.btc_price * (0.985 if side == "LONG" else 1.015), 2),
        "opened_at": time.strftime("%H:%M:%S"),
    }
    emoji = "🟢" if side == "LONG" else "🔴"
    log(f"{emoji} {source} > OPEN {side} {amount} BTC @ {S.btc_price}")

def close_position(reason: str = "Signal"):
    if not S.position:
        log(f"⚠️ {reason}: no open position")
        return
    p = S.position
    direction = 1 if p["side"] == "LONG" else -1
    pnl = round((S.btc_price - p["entry_price"]) * direction * p["amount"], 4)
    S.total_equity = round(S.total_equity + pnl, 2)
    S.total_profit_usdt = round(S.total_profit_usdt + pnl, 4)
    if pnl > 0:
        S.reserve_usdt = round(S.reserve_usdt + pnl * 0.25, 2)
    pnl_str = f"{'+' if pnl >= 0 else ''}{pnl:.4f} USDT"
    trade = {
        "time": time.strftime("%H:%M:%S"),
        "action": p["side"],
        "pnl": pnl_str,
    }
    S.recent_trades.append(trade)
    S.recent_trades = S.recent_trades[-20:]
    wins = sum(1 for t in S.recent_trades if not t["pnl"].startswith("-"))
    S.win_rate = round(wins / len(S.recent_trades) * 100, 1) if S.recent_trades else 68.4
    log(f"⚡ {reason} > Closed {p['side']} | PnL: {pnl_str}")
    S.position = None

# ============ AUTOPILOT ENGINE ============
cooldown = 0

def engine_loop():
    global cooldown
    while True:
        try:
            # تیک نوسان تصادفی قیمت
            S.btc_price = round(S.btc_price * (1 + random.uniform(-0.0004, 0.0006)), 2)

            # آپدیت RSI
            S.rsi = round(max(5.0, min(95.0, S.rsi + random.uniform(-3, 3))), 1)
            if S.rsi > 65:
                S.trend = "BULLISH"
            elif S.rsi < 40:
                S.trend = "BEARISH"
            else:
                S.trend = "NEUTRAL"

            # محاسبه زنده سود/ضرر پوزیشن باز
            if S.position:
                p = S.position
                direction = 1 if p["side"] == "LONG" else -1
                p["pnl"] = round((S.btc_price - p["entry_price"]) * direction * p["amount"], 4)

            # بررسی اتوپایلوت
            if S.autopilot:
                if S.position:
                    p = S.position
                    is_long = p["side"] == "LONG"
                    if (is_long and S.btc_price >= p["tp"]) or ((not is_long) and S.btc_price <= p["tp"]):
                        close_position("TP HIT")
                    elif (is_long and S.btc_price <= p["sl"]) or ((not is_long) and S.btc_price >= p["sl"]):
                        close_position("SL HIT")
                elif cooldown <= 0:
                    amount = 0.02
                    if S.rsi < 35:
                        open_position("LONG", amount, "AUTO")
                        cooldown = 3
                    elif S.rsi > 70:
                        open_position("SHORT", amount, "AUTO")
                        cooldown = 3
                else:
                    cooldown -= 1

            time.sleep(3)
        except Exception as e:
            log(f"❌ Engine Error: {e}")
            time.sleep(3)

threading.Thread(target=engine_loop, daemon=True).start()

# ============ API ============
class LoginRequest(BaseModel):
    pin: str

class ActionRequest(BaseModel):
    action: str
    amount: Optional[float] = 0.02

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/auth/login")
async def login(data: LoginRequest, response: Response):
    if data.pin == "402139235":
        response.set_cookie("session_token", "atria_session_ok", httponly=True)
        return {"status": "success"}
    raise HTTPException(401, "wrong pin")

@app.get("/api/public/status")
async def pub():
    return {"status": "RUNNING", "mode": "Paper Trading", "autopilot": S.autopilot}

@app.get("/api/telemetry")
@app.get("/api/dashboard/summary")
async def telemetry():
    return {
        "btc_price": S.btc_price,
        "current_price": S.btc_price,
        "total_equity": S.total_equity,
        "equity": S.total_equity,
        "reserve_usdt": S.reserve_usdt,
        "safe_profit": S.reserve_usdt,
        "win_rate": S.win_rate,
        "total_profit_usdt": S.total_profit_usdt,
        "rsi": S.rsi,
        "trend": S.trend,
        "autopilot": S.autopilot,
        "position": S.position,
        "active_position": S.position,
        "recent_trades": S.recent_trades,
        "logs": S.logs[-15:],
    }

@app.post("/api/action")
async def action(req: ActionRequest):
    global cooldown
    a = req.action.lower()
    if a == "buy":
        open_position("LONG", req.amount, "MANUAL")
    elif a == "sell":
        open_position("SHORT", req.amount, "MANUAL")
    elif a == "close":
        close_position("MANUAL")
    elif a == "panic":
        S.autopilot = False
        close_position("PANIC")
        log("🚨 PANIC: autopilot OFF, all positions closed")
    elif a == "toggle_autopilot":
        S.autopilot = not S.autopilot
        cooldown = 0
        if S.autopilot:
            log("⚙️ AUTOPILOT ON - engine started")
        else:
            log("⚙️ AUTOPILOT OFF")
    return {"status": "ok", "autopilot": S.autopilot}

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8080)
