import asyncio
import threading
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="AtriaTrade Pro Command Center")

templates = Jinja2Templates(directory="src/web/templates")

# State Management
state = {
    "bot_running": True,
    "auto_pilot": True,       # ترید خودکار فعال/غیرفعال
    "balance_usdt": 1000.0,
    "balance_btc": 0.05,
    "reserve_usdt": 0.0,       # صندوق امن سود
    "total_profit_usdt": 0.0,
    "btc_price": 63450.0,
    "rsi": 48.5,
    "trend": "NEUTRAL",
    "position": {"side": "FLAT", "amount": 0.0, "entry_price": 0.0, "pnl": 0.0},
    "recent_trades": [],
    "logs": [
        f"[{datetime.now().strftime('%H:%M:%S')}] سیستم با موفقیت راه‌اندازی شد.",
        f"[{datetime.now().strftime('%H:%M:%S')}] موتور استراتژی خودکار فعال است."
    ]
}

def log_event(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    state["logs"].append(f"[{ts}] {msg}")
    if len(state["logs"]) > 25:
        state["logs"].pop(0)

# Background AI Market & Auto-Trade Engine
def auto_trade_worker():
    import random
    while True:
        try:
            if state["bot_running"]:
                # 1. شبیه‌سازی تغییرات زنده قیمت و RSI
                delta = random.uniform(-180, 200)
                state["btc_price"] = round(state["btc_price"] + delta, 2)
                
                # محاسبه نوسان RSI بر اساس جهت قیمت
                rsi_delta = (delta / 200.0) * 3.5
                state["rsi"] = round(max(15.0, min(85.0, state["rsi"] + rsi_delta)), 1)
                
                if state["rsi"] > 65:
                    state["trend"] = "BULLISH (اشباع خرید)"
                elif state["rsi"] < 35:
                    state["trend"] = "BEARISH (اشباع فروش)"
                else:
                    state["trend"] = "CONSOLIDATING (خنثی)"

                # 2. محاسبه PnL پوزیشن باز در صورت وجود
                pos = state["position"]
                if pos["side"] == "LONG":
                    pos["pnl"] = round((state["btc_price"] - pos["entry_price"]) * pos["amount"], 2)
                elif pos["side"] == "SHORT":
                    pos["pnl"] = round((pos["entry_price"] - state["btc_price"]) * pos["amount"], 2)

                # 3. استراتژی خودکار Auto-Pilot
                if state["auto_pilot"]:
                    # خروج با سود حد سود (Take Profit > 15 USDT) یا حد ضرر (Stop Loss < -10 USDT)
                    if pos["side"] != "FLAT":
                        if pos["pnl"] >= 15.0:
                            # بستن با سود و انتقال 30% سود به صندوق ذخیره
                            profit = pos["pnl"]
                            reserve_share = round(profit * 0.30, 2)
                            state["reserve_usdt"] += reserve_share
                            state["balance_usdt"] += (pos["amount"] * state["btc_price"])
                            state["total_profit_usdt"] += profit
                            
                            trade_rec = {
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "action": f"CLOSE {pos['side']} (TP)",
                                "price": state["btc_price"],
                                "pnl": f"+{profit} USDT"
                            }
                            state["recent_trades"].insert(0, trade_rec)
                            log_event(f"🎯 حد سود فعال شد! سود: +{profit} USDT (ذخیره صندوق: {reserve_share} USDT)")
                            state["position"] = {"side": "FLAT", "amount": 0.0, "entry_price": 0.0, "pnl": 0.0}

                        elif pos["pnl"] <= -12.0:
                            loss = pos["pnl"]
                            state["balance_usdt"] += (pos["amount"] * state["btc_price"])
                            state["total_profit_usdt"] += loss
                            trade_rec = {
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "action": f"CLOSE {pos['side']} (SL)",
                                "price": state["btc_price"],
                                "pnl": f"{loss} USDT"
                            }
                            state["recent_trades"].insert(0, trade_rec)
                            log_event(f"🛑 حد ضرر محافظتی اجرا شد! نتیجه: {loss} USDT")
                            state["position"] = {"side": "FLAT", "amount": 0.0, "entry_price": 0.0, "pnl": 0.0}

                    # ورود به پوزیشن در شرایط بهینه
                    elif pos["side"] == "FLAT":
                        if state["rsi"] <= 30 and state["balance_usdt"] >= 1500:
                            # سیگنال خرید در اشباع فروش
                            qty = 0.02
                            cost = qty * state["btc_price"]
                            state["balance_usdt"] -= cost
                            state["position"] = {"side": "LONG", "amount": qty, "entry_price": state["btc_price"], "pnl": 0.0}
                            log_event(f"🤖 ورود خودکار به LONG در قیمت {state['btc_price']} (RSI={state['rsi']})")
                        elif state["rsi"] >= 70 and state["balance_btc"] >= 0.02:
                            # سیگنال فروش در اشباع خرید
                            qty = 0.02
                            state["position"] = {"side": "SHORT", "amount": qty, "entry_price": state["btc_price"], "pnl": 0.0}
                            log_event(f"🤖 ورود خودکار به SHORT در قیمت {state['btc_price']} (RSI={state['rsi']})")

            time.sleep(3)
        except Exception as e:
            time.sleep(3)

# استارت تِرِد پس‌زمینه
worker_thread = threading.Thread(target=auto_trade_worker, daemon=True)
worker_thread.start()

class ActionPayload(BaseModel):
    action: str
    symbol: str = "BTCUSDT"
    amount: float = 0.02

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/telemetry")
async def get_telemetry():
    total_equity = round(
        state["balance_usdt"] + 
        (state["balance_btc"] + state["position"]["amount"]) * state["btc_price"] + 
        state["reserve_usdt"], 
        2
    )
    return {
        "status": "ONLINE" if state["bot_running"] else "PAUSED",
        "bot_running": state["bot_running"],
        "auto_pilot": state["auto_pilot"],
        "btc_price": f"{state['btc_price']:,.2f}",
        "balance_usdt": f"{state['balance_usdt']:,.2f}",
        "balance_btc": f"{state['balance_btc']:.4f}",
        "reserve_usdt": f"{state['reserve_usdt']:,.2f}",
        "total_profit_usdt": f"{state['total_profit_usdt']:+,.2f}",
        "total_equity": f"{total_equity:,.2f}",
        "rsi": state["rsi"],
        "trend": state["trend"],
        "position": state["position"],
        "recent_trades": state["recent_trades"][:6],
        "logs": state["logs"][-15:]
    }

@app.post("/api/action")
async def execute_action(payload: ActionPayload):
    act = payload.action
    if act == "toggle_bot":
        state["bot_running"] = not state["bot_running"]
        log_event(f"وضعیت ربات تغییر کرد: {'روشن' if state['bot_running'] else 'متوقف'}")
    elif act == "toggle_auto":
        state["auto_pilot"] = not state["auto_pilot"]
        log_event(f"حالت ترید خودکار (Auto-Pilot): {'فعال' if state['auto_pilot'] else 'غیرفعال'}")
    elif act == "buy":
        qty = payload.amount
        cost = qty * state["btc_price"]
        if state["balance_usdt"] >= cost:
            state["balance_usdt"] -= cost
            state["balance_btc"] += qty
            log_event(f"خرید دستی موفق: {qty} BTC در {state['btc_price']}")
        else:
            log_event("خطا: موجودی تتر ناکافی است.")
    elif act == "sell":
        qty = payload.amount
        if state["balance_btc"] >= qty:
            state["balance_btc"] -= qty
            revenue = qty * state["btc_price"]
            state["balance_usdt"] += revenue
            log_event(f"فروش دستی موفق: {qty} BTC در {state['btc_price']}")
        else:
            log_event("خطا: موجودی بیت‌کوین ناکافی است.")
    elif act == "panic":
        state["bot_running"] = False
        state["auto_pilot"] = False
        if state["position"]["side"] != "FLAT":
            state["balance_usdt"] += state["position"]["amount"] * state["btc_price"]
            state["position"] = {"side": "FLAT", "amount": 0.0, "entry_price": 0.0, "pnl": 0.0}
        log_event("🚨 توقف اضطراری (PANIC)! پوزیشن‌ها بسته و موتور متوقف شد.")
    return {"status": "success"}
