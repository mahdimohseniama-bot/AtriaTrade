import uvicorn
import random
import time
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="AtriaTrade Enterprise Dashboard")
templates = Jinja2Templates(directory="src/web/templates")

# وضعیت سراسری ربات و پورتفوی
system_state = {
    "bot_status": "RUNNING",  # RUNNING, PAUSED, STOPPED
    "mode": "PAPER_TRADING",
    "balance": 10000.0,
    "profit_reserve": 250.0,
    "daily_pnl": 187.56,
    "daily_pnl_pct": 1.88,
    "start_time": time.time(),
}

current_btc_price = 63927.13
price_history = [current_btc_price + random.uniform(-60, 60) for _ in range(30)]

# متغیرهای تکنیکال
tech_state = {
    "rsi": 54.2,
    "macd_signal": "BULLISH",
    "market_trend": "صعودی ملایم (Uptrend)",
    "ai_confidence": "87%"
}

positions = [
    {"symbol": "BTC/USDT", "side": "BUY", "entry": 63920.0, "current": 63927.13, "amount": 0.05, "pnl": 0.35, "pnl_pct": 0.01, "sl": 63200.0, "tp": 65500.0},
    {"symbol": "ETH/USDT", "side": "BUY", "entry": 3450.0, "current": 3485.0, "amount": 1.20, "pnl": 42.00, "pnl_pct": 1.01, "sl": 3390.0, "tp": 3600.0}
]

logs_stream = [
    {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO", "source": "ENGINE", "msg": "موتور Paper Trading فعال و پایدار است."},
    {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": "SUCCESS", "source": "RESERVE", "msg": "صندوق سود امن فعال (۲۵۰ تتر)."}
]

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "state": system_state
    })

@app.get("/api/telemetry")
async def get_telemetry():
    global price_history, current_btc_price
    
    # نوسان قیمت زنده
    delta = random.uniform(-30, 35)
    current_btc_price = round(current_btc_price + delta, 2)
    price_history.append(current_btc_price)
    if len(price_history) > 50:
        price_history.pop(0)

    # آپدیت RSI و سیگنال تکنیکال
    tech_state["rsi"] = round(max(15, min(85, tech_state["rsi"] + random.uniform(-2.5, 2.5))), 1)
    if tech_state["rsi"] > 70:
        tech_state["macd_signal"] = "OVERBOUGHT (اشباع خرید)"
        tech_state["market_trend"] = "احتمال اصلاح نزولی"
    elif tech_state["rsi"] < 30:
        tech_state["macd_signal"] = "OVERSOLD (اشباع فروش)"
        tech_state["market_trend"] = "فرصت خرید قوی"
    else:
        tech_state["macd_signal"] = "BULLISH (صعودی)"
        tech_state["market_trend"] = "روند متعادل مثبت"

    # آپدیت PnL پوزیشن‌ها
    total_pos_pnl = 0.0
    for pos in positions:
        if pos["symbol"] == "BTC/USDT":
            pos["current"] = current_btc_price
            diff = (pos["current"] - pos["entry"]) if pos["side"] == "BUY" else (pos["entry"] - pos["current"])
            pos["pnl"] = round(diff * pos["amount"], 2)
            pos["pnl_pct"] = round((diff / pos["entry"]) * 100, 2)
        total_pos_pnl += pos["pnl"]

    uptime_sec = int(time.time() - system_state["start_time"])
    uptime_str = str(datetime.timedelta(seconds=uptime_sec))

    return JSONResponse(content={
        "price": current_btc_price,
        "chart_prices": price_history,
        "chart_labels": [f"-{len(price_history)-i}s" for i in range(len(price_history))],
        "balance": round(system_state["balance"], 2),
        "reserve": round(system_state["profit_reserve"], 2),
        "daily_pnl": round(system_state["daily_pnl"] + total_pos_pnl, 2),
        "daily_pnl_pct": round(((system_state["daily_pnl"] + total_pos_pnl) / system_state["balance"]) * 100, 2),
        "bot_status": system_state["bot_status"],
        "uptime": uptime_str,
        "tech": tech_state,
        "system_metrics": {
            "termux_cpu": f"{random.randint(14, 29)}%",
            "termux_ram": f"{random.randint(220, 260)} MB / 6 GB",
            "threads": 8
        },
        "exchanges": {
            "nobitex": {"status": "ONLINE", "ping": f"{random.randint(48, 85)}ms"},
            "binance": {"status": "ONLINE", "ping": f"{random.randint(105, 140)}ms"},
            "mock_engine": {"status": "ACTIVE", "ping": "1ms"}
        },
        "positions": positions,
        "logs": logs_stream[-12:]
    })

@app.post("/api/action/{action_name}")
async def handle_action(action_name: str, payload: dict = None):
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    
    if action_name == "start":
        system_state["bot_status"] = "RUNNING"
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "CONTROL", "msg": "ربات فعال شد - تحلیل لحظه‌ای بازار در جریان است."})
    elif action_name == "pause":
        system_state["bot_status"] = "PAUSED"
        logs_stream.append({"time": now_str, "level": "WARN", "source": "CONTROL", "msg": "ربات متوقف شد - وضعیت تریدها حفظ می‌گردد."})
    elif action_name == "panic":
        system_state["bot_status"] = "STOPPED"
        positions.clear()
        logs_stream.append({"time": now_str, "level": "DANGER", "source": "PANIC", "msg": "🚨 خروج اضطراری! تمام پوزیشن‌ها بسته و دارایی‌ها نقد شدند."})
    elif action_name == "deposit":
        system_state["balance"] += 1000.0
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "WALLET", "msg": "واریز ۱۰۰۰ تتر شبیه‌ساز به بالانس فعال انجام شد."})
    elif action_name == "withdraw_profit":
        if system_state["profit_reserve"] > 0:
            val = system_state["profit_reserve"]
            system_state["profit_reserve"] = 0.0
            logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "RESERVE", "msg": f"برداشت {val}$ سود امن با موفقیت ثبت شد."})
        else:
            logs_stream.append({"time": now_str, "level": "WARN", "source": "RESERVE", "msg": "موجودی صندوق سود خالی است."})
    elif action_name == "trade_buy":
        cost = current_btc_price * 0.02
        if system_state["balance"] >= cost:
            system_state["balance"] -= cost
            positions.append({"symbol": "BTC/USDT", "side": "BUY", "entry": current_btc_price, "current": current_btc_price, "amount": 0.02, "pnl": 0.0, "pnl_pct": 0.0, "sl": round(current_btc_price*0.985, 1), "tp": round(current_btc_price*1.03, 1)})
            logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "ORDER", "msg": f"سفارش خرید دستی 0.02 BTC در قیمت ${current_btc_price} ثبت گردید."})
    elif action_name == "trade_sell":
        positions.append({"symbol": "BTC/USDT", "side": "SELL", "entry": current_btc_price, "current": current_btc_price, "amount": 0.02, "pnl": 0.0, "pnl_pct": 0.0, "sl": round(current_btc_price*1.015, 1), "tp": round(current_btc_price*0.97, 1)})
        logs_stream.append({"time": now_str, "level": "WARN", "source": "ORDER", "msg": f"سفارش فروش دستی 0.02 BTC در قیمت ${current_btc_price} ثبت گردید."})

    return {"status": "OK", "bot_status": system_state["bot_status"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
