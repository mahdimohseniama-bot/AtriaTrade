import uvicorn
import random
import time
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="AtriaTrade Enterprise Dashboard")
templates = Jinja2Templates(directory="src/web/templates")

# وضعیت کلی و بالانس
system_state = {
    "bot_status": "RUNNING",
    "mode": "PAPER_TRADING",
    "balance": 10000.0,
    "profit_reserve": 250.0,
    "daily_pnl": 145.20,
    "daily_pnl_pct": 1.45,
    "start_time": time.time(),
}

current_btc_price = 63920.0
price_history = [current_btc_price + random.uniform(-100, 100) for _ in range(30)]

positions = [
    {"symbol": "BTC/USDT", "side": "BUY", "entry": 63920.0, "current": 63921.84, "amount": 0.05, "pnl": 0.09, "pnl_pct": 0.00, "sl": 63200.0, "tp": 65500.0},
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
    
    # نوسان قیمت
    delta = random.uniform(-25, 30)
    current_btc_price = round(current_btc_price + delta, 2)
    price_history.append(current_btc_price)
    if len(price_history) > 50:
        price_history.pop(0)

    # آپدیت سود پوزیشن‌ها
    total_unrealized_pnl = 0.0
    for pos in positions:
        if pos["symbol"] == "BTC/USDT":
            pos["current"] = current_btc_price
            diff = pos["current"] - pos["entry"] if pos["side"] == "BUY" else pos["entry"] - pos["current"]
            pos["pnl"] = round(diff * pos["amount"], 2)
            pos["pnl_pct"] = round((diff / pos["entry"]) * 100, 2)
        total_unrealized_pnl += pos["pnl"]

    uptime_sec = int(time.time() - system_state["start_time"])
    uptime_str = str(datetime.timedelta(seconds=uptime_sec))

    return JSONResponse(content={
        "price": current_btc_price,
        "chart_prices": price_history,
        "chart_labels": [f"-{len(price_history)-i}s" for i in range(len(price_history))],
        "balance": round(system_state["balance"], 2),
        "reserve": round(system_state["profit_reserve"], 2),
        "daily_pnl": round(system_state["daily_pnl"] + total_unrealized_pnl, 2),
        "daily_pnl_pct": round(((system_state["daily_pnl"] + total_unrealized_pnl) / system_state["balance"]) * 100, 2),
        "bot_status": system_state["bot_status"],
        "uptime": uptime_str,
        "system_metrics": {
            "termux_cpu": f"{random.randint(15, 35)}%",
            "termux_ram": f"{random.randint(210, 285)} MB / 6 GB",
            "threads": 8
        },
        "exchanges": {
            "nobitex": {"status": "ONLINE", "ping": f"{random.randint(45, 90)}ms"},
            "binance": {"status": "ONLINE", "ping": f"{random.randint(110, 175)}ms"},
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
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "CONTROL", "msg": "ربات شروع به کار کرد."})
    elif action_name == "pause":
        system_state["bot_status"] = "PAUSED"
        logs_stream.append({"time": now_str, "level": "WARN", "source": "CONTROL", "msg": "ربات متوقف شد."})
    elif action_name == "panic":
        system_state["bot_status"] = "STOPPED"
        positions.clear()
        logs_stream.append({"time": now_str, "level": "DANGER", "source": "PANIC", "msg": "🚨 تمام پوزیشن‌ها بسته و نقد شدند."})
    elif action_name == "deposit":
        system_state["balance"] += 1000.0
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "WALLET", "msg": "واریز ۱۰۰۰ تتر انجام شد."})
    elif action_name == "withdraw_profit":
        if system_state["profit_reserve"] > 0:
            val = system_state["profit_reserve"]
            system_state["profit_reserve"] = 0.0
            logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "RESERVE", "msg": f"برداشت {val}$ سود امن با موفقیت ثبت شد."})
    elif action_name == "trade_buy":
        cost = current_btc_price * 0.02
        if system_state["balance"] >= cost:
            system_state["balance"] -= cost
            positions.append({"symbol": "BTC/USDT", "side": "BUY", "entry": current_btc_price, "current": current_btc_price, "amount": 0.02, "pnl": 0.0, "pnl_pct": 0.0, "sl": round(current_btc_price*0.98, 1), "tp": round(current_btc_price*1.03, 1)})
            logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "ORDER", "msg": f"سفارش خرید دستی 0.02 BTC در قیمت ${current_btc_price} باز شد."})
    elif action_name == "trade_sell":
        cost = current_btc_price * 0.02
        positions.append({"symbol": "BTC/USDT", "side": "SELL", "entry": current_btc_price, "current": current_btc_price, "amount": 0.02, "pnl": 0.0, "pnl_pct": 0.0, "sl": round(current_btc_price*1.02, 1), "tp": round(current_btc_price*0.97, 1)})
        logs_stream.append({"time": now_str, "level": "WARN", "source": "ORDER", "msg": f"سفارش فروش دستی 0.02 BTC در قیمت ${current_btc_price} ثبت شد."})

    return {"status": "OK", "bot_status": system_state["bot_status"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
