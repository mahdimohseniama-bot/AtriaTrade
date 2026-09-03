import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="AtriaTrade Paper Trading")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def new_position() -> dict[str, Any]:
    return {
        "side": "FLAT",
        "entry_price": 0.0,
        "amount": 0.0,
        "highest_price": 0.0,
        "lowest_price": 0.0,
        "unrealized_pnl": 0.0,
        "tp_price": 0.0,
        "sl_price": 0.0,
    }

state: dict[str, Any] = {
    "mode": "PAPER",
    "symbol": "BTCUSDT",
    "usdt_balance": 10000.0,
    "btc_balance": 0.0,
    "reserve_vault_usdt": 0.0,
    "total_realized_profit_usdt": 0.0,
    "winning_trades": 0,
    "losing_trades": 0,
    "total_closed_trades": 0,
    "auto_pilot": True,
    "panic_mode": False,
    "current_price": 63330.0,
    "price_history": [63330.0] * 60,
    "ema_fast": 63330.0,
    "ema_slow": 63330.0,
    "rsi": 50.0,
    "market_trend": "NEUTRAL",
    "position": new_position(),
    "recent_trades": [],
    "logs": [f"[{datetime.now().strftime("%H:%M:%S")} AtriaTrade online]"],
}

def log_event(message: str) -> None:
    t = datetime.now().strftime("%H:%M:%S")
    state["logs"].append(f"[{t}] {message}")
    state["logs"] = state["logs"][-40:]

def calculate_rsi(prices: list[float], period: int = 14) -> float:
    if len(prices) <= period:
        return 50.0
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent_changes = changes[-period:]
    gains = [max(c, 0.0) for c in recent_changes]
    losses = [max(-c, 0.0) for c in recent_changes]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def calculate_ema(prices: list[float], period: int) -> float:
    if not prices:
        return 0.0
    multiplier = 2.0 / (period + 1.0)
    ema = prices[0]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
    return ema

def calculate_indicators():
    prices = state["price_history"]
    rsi = calculate_rsi(prices, 14)
    fast = calculate_ema(prices, 9)
    slow = calculate_ema(prices, 21)
    if fast > slow and rsi >= 52:
        trend = "BULLISH"
    elif fast < slow and rsi <= 48:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    state["ema_fast"] = fast
    state["ema_slow"] = slow
    return round(rsi, 2), round(fast, 2), round(slow, 2), trend

def open_long(amount: float, price: float) -> bool:
    cost = amount * price
    if state["position"]["side"] != "FLAT":
        return False
    if state["usdt_balance"] < cost:
        log_event("Insufficient USDT")
        return False
    state["usdt_balance"] -= cost
    state["btc_balance"] += amount
    state["position"] = {
        "side": "LONG",
        "entry_price": price,
        "amount": amount,
        "highest_price": price,
        "lowest_price": price,
        "unrealized_pnl": 0.0,
        "tp_price": round(price * 1.012, 2),
        "sl_price": round(price * 0.993, 2),
    }
    log_event(f"Open LONG {amount} BTC @ {price}")
    return True

def open_short(amount: float, price: float) -> bool:
    if state["position"]["side"] != "FLAT":
        return False
    state["position"] = {
        "side": "SHORT",
        "entry_price": price,
        "amount": amount,
        "highest_price": price,
        "lowest_price": price,
        "unrealized_pnl": 0.0,
        "tp_price": round(price * 0.988, 2),
        "sl_price": round(price * 1.007, 2),
    }
    log_event(f"Open SHORT {amount} BTC @ {price}")
    return True

def execute_close_position(reason: str) -> None:
    pos = state["position"]
    if pos["side"] == "FLAT":
        return
    cp = state["current_price"]
    side = pos["side"]
    amt = pos["amount"]
    ep = pos["entry_price"]
    if side == "LONG":
        rev = amt * cp
        cost = amt * ep
        profit = rev - cost
        state["usdt_balance"] += rev
        state["btc_balance"] = max(0.0, state["btc_balance"] - amt)
    else:
        profit = (ep - cp) * amt
        state["usdt_balance"] += profit

    state["total_closed_trades"] += 1
    state["total_realized_profit_usdt"] += profit
    if profit > 0:
        state["winning_trades"] += 1
        cut = profit * 0.30
        state["reserve_vault_usdt"] += cut
        state["usdt_balance"] -= cut
    else:
        state["losing_trades"] += 1

    trade = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": f"Close {side}",
        "reason": reason,
        "price": f"{cp:,.2f}",
        "pnl": round(profit, 2),
        "pnl_text": f"{profit:+.2f} USDT",
    }
    state["recent_trades"].insert(0, trade)
    state["recent_trades"] = state["recent_trades"][:20]
    log_event(f"Closed {side} ({reason}) PnL: {profit:+.2f}")
    state["position"] = new_position()

def update_open_position() -> None:
    pos = state["position"]
    if pos["side"] == "FLAT":
        return
    cp = state["current_price"]
    ep = pos["entry_price"]
    amt = pos["amount"]
    if pos["side"] == "LONG":
        pos["unrealized_pnl"] = round((cp - ep) * amt, 2)
        if cp > pos["highest_price"]:
            pos["highest_price"] = cp
            pos["sl_price"] = max(pos["sl_price"], round(cp * 0.993, 2))
        if cp >= pos["tp_price"]:
            execute_close_position("TP")
        elif cp <= pos["sl_price"]:
            execute_close_position("SL/Trailing")
    elif pos["side"] == "SHORT":
        pos["unrealized_pnl"] = round((ep - cp) * amt, 2)
        if pos["lowest_price"] == 0.0 or cp < pos["lowest_price"]:
            pos["lowest_price"] = cp
            tr = round(cp * 1.007, 2)
            pos["sl_price"] = tr if pos["sl_price"] == 0.0 else min(pos["sl_price"], tr)
        if cp <= pos["tp_price"]:
            execute_close_position("TP")
        elif cp >= pos["sl_price"]:
            execute_close_position("SL/Trailing")

def try_auto_entry(rsi: float, fast: float, slow: float) -> None:
    if not state["auto_pilot"] or state["panic_mode"] or state["position"]["side"] != "FLAT":
        return
    amt = 0.02
    cp = state["current_price"]
    if rsi <= 35 and fast >= slow:
        open_long(amt, cp)
    elif rsi >= 65 and fast <= slow:
        open_short(amt, cp)

async def market_loop() -> None:
    while True:
        try:
            prev = state["current_price"]
            drift = (63330.0 - prev) * 0.002
            noise = random.uniform(-45.0, 48.0)
            new_p = max(1000.0, round(prev + drift + noise, 2))
            state["current_price"] = new_p
            state["price_history"].append(new_p)
            state["price_history"] = state["price_history"][-120:]
            rsi, fast, slow, trend = calculate_indicators()
            state["rsi"] = rsi
            state["market_trend"] = trend
            update_open_position()
            if state["position"]["side"] == "FLAT":
                try_auto_entry(rsi, fast, slow)
        except Exception as e:
            log_event(f"Market loop error: {e}")
        await asyncio.sleep(1.8)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_loop())

class ActionPayload(BaseModel):
    action: str
    symbol: str = "BTCUSDT"
    amount: float = Field(default=0.02, gt=0.0, le=1.0)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/telemetry")
async def get_telemetry():
    cp = state["current_price"]
    pos = state["position"]
    pos_pnl = pos["unrealized_pnl"] if pos["side"] != "FLAT" else 0.0
    equity = state["usdt_balance"] + (state["btc_balance"] * cp) + pos_pnl
    trades = state["total_closed_trades"]
    wr = (state["winning_trades"] / trades * 100.0) if trades else 0.0
    return {
        "mode": state["mode"],
        "symbol": state["symbol"],
        "btc_price": f"{cp:,.2f}",
        "total_equity": f"{equity:,.2f}",
        "usdt_balance": f"{state["usdt_balance"]:,.2f}",
        "btc_balance": round(state["btc_balance"], 8),
        "reserve_usdt": f"{state["reserve_vault_usdt"]:,.2f}",
        "total_profit_usdt": f"{state["total_realized_profit_usdt"]:+.2f}",
        "winning_trades": state["winning_trades"],
        "losing_trades": state["losing_trades"],
        "total_closed_trades": trades,
        "win_rate": round(wr, 1),
        "rsi": state["rsi"],
        "ema_fast": round(state["ema_fast"], 2),
        "ema_slow": round(state["ema_slow"], 2),
        "trend": state["market_trend"],
        "auto_pilot": state["auto_pilot"],
        "panic_mode": state["panic_mode"],
        "position": {
            "side": pos["side"],
            "entry_price": f"${pos["entry_price"]:,.2f}",
            "amount": pos["amount"],
            "pnl": pos["unrealized_pnl"],
            "tp": f"${pos["tp_price"]:,.2f}",
            "sl": f"${pos["sl_price"]:,.2f}",
        },
        "recent_trades": state["recent_trades"],
        "logs": state["logs"],
    }

@app.post("/api/action")
async def handle_action(payload: ActionPayload):
    act = payload.action
    cp = state["current_price"]
    if act == "toggle_auto":
        if state["panic_mode"]:
            return {"status": "blocked", "message": "Panic active"}
        state["auto_pilot"] = not state["auto_pilot"]
        log_event(f"Auto-pilot: {state["auto_pilot"]}")
        return {"status": "ok", "auto_pilot": state["auto_pilot"]}
    if act == "panic":
        state["auto_pilot"] = False
        state["panic_mode"] = True
        execute_close_position("PANIC")
        log_event("PANIC executed")
        return {"status": "panic_executed", "panic_mode": True}
    if act == "buy":
        if state["position"]["side"] != "FLAT":
            return {"status": "blocked", "message": "Close open position first"}
        ok = open_long(payload.amount, cp)
        return {"status": "ok" if ok else "rejected", "action": "buy"}
    if act == "sell":
        if state["position"]["side"] == "LONG":
            execute_close_position("Manual Sell")
            return {"status": "ok", "action": "sell"}
        if state["position"]["side"] == "FLAT":
            ok = open_short(payload.amount, cp)
            return {"status": "ok" if ok else "rejected", "action": "sell"}
        return {"status": "blocked", "message": "Invalid state for sell"}
    if act == "close":
        execute_close_position("Manual Close")
        return {"status": "ok", "action": "close"}
    return {"status": "unknown"}
