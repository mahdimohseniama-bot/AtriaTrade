import uvicorn
import random
import time
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="AtriaTrade Enterprise Dashboard")
templates = Jinja2Templates(directory="src/web/templates")

# وضعیت سراسری سیستم
system_state = {
    "bot_status": "RUNNING",  # RUNNING, PAUSED, STOPPED
    "mode": "PAPER_TRADING",
    "balance": 10000.0,
    "profit_reserve": 250.0,
    "daily_pnl": 145.20,
    "daily_pnl_pct": 1.45,
    "active_positions_count": 2,
    "start_time": time.time(),
}

price_history = [64000.0 + random.uniform(-100, 100) for _ in range(30)]

positions = [
    {"symbol": "BTC/USDT", "side": "BUY", "entry": 63920.0, "current": 64116.0, "amount": 0.05, "pnl": 9.80, "pnl_pct": 0.31, "sl": 63200.0, "tp": 65500.0},
    {"symbol": "ETH/USDT", "side": "BUY", "entry": 3450.0, "current": 3485.0, "amount": 1.20, "pnl": 42.00, "pnl_pct": 1.01, "sl": 3390.0, "tp": 3600.0}
]

logs_stream = [
    {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO", "source": "ENGINE", "msg": "موتور Paper Trading فعال است."},
    {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": "SUCCESS", "source": "RESERVE", "msg": "سود امن ۲۵۰ تتر به صندوق ذخیره منتقل شد."},
    {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": "INFO", "source": "RISK", "msg": "سقف ریسک روزانه زیر ۲٪ تنظیم شده است."}
]

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "state": system_state
    })

@app.get("/api/telemetry")
async def get_telemetry():
    global price_history
    # نوسان قیمت زنده
    new_price = round(price_history[-1] + random.uniform(-35, 40), 2)
    price_history.append(new_price)
    if len(price_history) > 50:
        price_history.pop(0)

    # به‌روزرسانی پوزیشن اول بر اساس قیمت جدید
    positions[0]["current"] = new_price
    positions[0]["pnl"] = round((new_price - positions[0]["entry"]) * positions[0]["amount"], 2)
    positions[0]["pnl_pct"] = round(((new_price - positions[0]["entry"]) / positions[0]["entry"]) * 100, 2)

    uptime_sec = int(time.time() - system_state["start_time"])
    uptime_str = str(datetime.timedelta(seconds=uptime_sec))

    # مانیتورینگ سخت‌افزار و صرافی‌ها
    telemetry_data = {
        "price": new_price,
        "chart_prices": price_history,
        "chart_labels": [f"-{len(price_history)-i}s" for i in range(len(price_history))],
        "balance": round(system_state["balance"], 2),
        "reserve": round(system_state["profit_reserve"], 2),
        "daily_pnl": round(system_state["daily_pnl"] + random.uniform(-0.5, 0.8), 2),
        "daily_pnl_pct": round(system_state["daily_pnl_pct"], 2),
        "bot_status": system_state["bot_status"],
        "uptime": uptime_str,
        "system_metrics": {
            "termux_cpu": f"{random.randint(12, 38)}%",
            "termux_ram": f"{random.randint(180, 290)} MB / 6 GB",
            "threads": 8
        },
        "exchanges": {
            "nobitex": {"status": "ONLINE", "ping": f"{random.randint(45, 95)}ms"},
            "binance": {"status": "ONLINE", "ping": f"{random.randint(110, 180)}ms"},
            "mock_engine": {"status": "ACTIVE", "ping": "1ms"}
        },
        "positions": positions,
        "logs": logs_stream[-10:]
    }
    return JSONResponse(content=telemetry_data)

@app.post("/api/action/{action_name}")
async def handle_action(action_name: str, payload: dict = None):
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    
    if action_name == "start":
        system_state["bot_status"] = "RUNNING"
        msg = "دستور شروع صادر شد - موتور تحلیل در حال پردازش مارکت."
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "CONTROL", "msg": msg})
    elif action_name == "pause":
        system_state["bot_status"] = "PAUSED"
        msg = "ربات موقتاً متوقف شد - پوزیشن‌های باز حفظ می‌شوند."
        logs_stream.append({"time": now_str, "level": "WARN", "source": "CONTROL", "msg": msg})
    elif action_name == "panic":
        system_state["bot_status"] = "STOPPED"
        msg = "خروج اضطراری! تمام پوزیشن‌ها نقد و فعالیت تریدینگ لغو گردید."
        positions.clear()
        logs_stream.append({"time": now_str, "level": "DANGER", "source": "PANIC", "msg": msg})
    elif action_name == "deposit":
        system_state["balance"] += 1000.0
        msg = "واریز شبیه‌ساز: ۱۰۰۰ تتر به بالانس افزوده شد."
        logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "WALLET", "msg": msg})
    elif action_name == "withdraw_profit":
        if system_state["profit_reserve"] > 50:
            withdrawn = system_state["profit_reserve"]
            system_state["profit_reserve"] = 0.0
            msg = f"برداشت موفق: مبلغ {withdrawn} تتر سود امن برداشت و ثبت شد."
            logs_stream.append({"time": now_str, "level": "SUCCESS", "source": "RESERVE", "msg": msg})
        else:
            msg = "موجودی صندوق سود کمتر از حداقل ۵۰ تتر است."
            logs_stream.append({"time": now_str, "level": "WARN", "source": "RESERVE", "msg": msg})
    else:
        msg = "عملیات نامعتبر است."
    
    return {"status": "OK", "message": msg, "bot_status": system_state["bot_status"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
