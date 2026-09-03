import asyncio
import random
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
import csv
import io
import sqlite3
import os

app = FastAPI(title="AtriaTrade Pro")

# پایگاه داده SQLite برای ذخیره قطعی تاریخچه معاملات
DB_PATH = "data/trading.db"
os.makedirs("data", exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_str TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl REAL
            )
        """)
        conn.commit()

init_db()

state = {
    "price": 96350.0,
    "equity": 10000.0,
    "safe_profit": 0.0,
    "rsi": 54.0,
    "trend": "صعودی 🟢",
    "autopilot": True,
    "price_history": [96200.0, 96280.0, 96310.0, 96350.0],
    "active_position": None,
    "trades": [],
    "logs": ["[سیستم] موتور هوشمند ترید AtriaTrade فعال شد."]
}

def log(msg: str):
    t = datetime.now().strftime("%H:%M:%S")
    state["logs"].append(f"[{t}] {msg}")
    if len(state["logs"]) > 35:
        state["logs"].pop(0)

def load_initial_trades():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT time_str, side, entry_price, exit_price, pnl FROM trades ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        state["trades"] = [{"time_str": r[0], "side": r[1], "entry_price": r[2], "exit_price": r[3], "pnl": r[4]} for r in rows]

load_initial_trades()

async def market_and_strategy_loop():
    while True:
        await asyncio.sleep(2)
        # نوسان قیمت شبیه‌سازی بازار
        delta = random.uniform(-40.0, 45.0)
        state["price"] = round(state["price"] + delta, 2)
        state["price_history"].append(state["price"])
        if len(state["price_history"]) > 40:
            state["price_history"].pop(0)
            
        # محاسبه شاخص RSI
        rsi_change = random.uniform(-3.0, 3.5)
        state["rsi"] = round(max(20.0, min(85.0, state["rsi"] + rsi_change)), 1)
        state["trend"] = "صعودی 🟢" if state["rsi"] >= 50 else "نزولی 🔴"
        
        # محاسبه PnL پوزیشن فعال
        pos = state["active_position"]
        if pos:
            cur_p = state["price"]
            ent_p = pos["entry_price"]
            amt = pos["amount"]
            pnl = (cur_p - ent_p) * amt if pos["side"] == "BUY" else (ent_p - cur_p) * amt
            pos["pnl"] = round(pnl, 2)
            pos["pnl_pct"] = round((pnl / (ent_p * amt)) * 100, 2)
            state["equity"] = round(10000.0 + state["safe_profit"] + pnl, 2)
            
            # خروج بر اساس حد سود و ضرر یا اشباع RSI در اتوپایلوت
            if state["autopilot"]:
                if pos["pnl_pct"] >= 1.2 or (pos["side"] == "BUY" and state["rsi"] > 72):
                    log(f"🎯 سیگنال خروج هوشمند (Take Profit): بستن {pos['side']} با سود ${pos['pnl']}")
                    await close_pos()
                elif pos["pnl_pct"] <= -1.0 or (pos["side"] == "BUY" and state["rsi"] < 35):
                    log(f"🛑 خروج اضطراری و حد ضرر (Stop Loss): ${pos['pnl']}")
                    await close_pos()
        else:
            # تصمیم‌گیری برای ورود هوشمند (Auto-Pilot Strategy)
            if state["autopilot"]:
                if state["rsi"] < 38:
                    log(f"🤖 سیگنال خرید خودکار RSI اشباع فروش ({state['rsi']})")
                    await place_order_internal("BUY", 0.02)
                elif state["rsi"] > 68:
                    log(f"🤖 سیگنال فروش خودکار RSI اشباع خرید ({state['rsi']})")
                    await place_order_internal("SELL", 0.02)

async def place_order_internal(side: str, amount: float = 0.02):
    if state["active_position"] is not None:
        return
    state["active_position"] = {
        "side": side,
        "entry_price": state["price"],
        "amount": amount,
        "pnl": 0.0,
        "pnl_pct": 0.0
    }
    log(f"معامله {side} به حجم {amount} BTC در قیمت ${state['price']:,.2f} ثبت شد.")

@app.on_event("startup")
async def startup():
    asyncio.create_task(market_and_strategy_loop())

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("src/web/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/telemetry")
async def telemetry():
    return {
        "current_price": state["price"],
        "equity": state["equity"],
        "safe_profit": state["safe_profit"],
        "rsi": state["rsi"],
        "trend": state["trend"],
        "autopilot": state["autopilot"],
        "price_history": state["price_history"],
        "active_position": state["active_position"],
        "recent_trades": state["trades"],
        "logs": state["logs"]
    }

class OrderModel(BaseModel):
    side: str
    amount: float = 0.02

@app.post("/api/order/manual")
async def place_order(o: OrderModel):
    await place_order_internal(o.side.upper(), o.amount)
    return {"status": "ok"}

@app.post("/api/order/close")
async def close_pos():
    pos = state["active_position"]
    if pos:
        pnl = pos["pnl"]
        t_str = datetime.now().strftime("%H:%M:%S")
        trade_record = {
            "time_str": t_str,
            "side": pos["side"],
            "entry_price": pos["entry_price"],
            "exit_price": state["price"],
            "pnl": pnl
        }
        state["trades"].insert(0, trade_record)
        if len(state["trades"]) > 25:
            state["trades"].pop()

        # ذخیره در دیتابیس
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO trades (time_str, side, entry_price, exit_price, pnl) VALUES (?, ?, ?, ?, ?)",
                (t_str, pos["side"], pos["entry_price"], state["price"], pnl)
            )
            conn.commit()

        # منطق انتقال به صندوق امن سود
        if pnl > 0:
            saved = round(pnl * 0.3, 2)
            state["safe_profit"] = round(state["safe_profit"] + saved, 2)
            log(f"💰 معامله بسته شد | سود کل: +${pnl} | انتقال ۳۰٪ (${saved}) به صندوق امن")
        else:
            log(f"⚠️ معامله بسته شد با PnL: ${pnl}")
        
        state["active_position"] = None
        state["equity"] = round(10000.0 + state["safe_profit"], 2)
    return {"status": "ok"}

@app.post("/api/autopilot/toggle")
async def toggle_auto():
    state["autopilot"] = not state["autopilot"]
    st_text = "فعال" if state["autopilot"] else "غیرفعال"
    log(f"⚡ اتوپایلوت توسط کاربر {st_text} شد.")
    return {"autopilot": state["autopilot"]}

@app.post("/api/panic")
async def panic():
    state["autopilot"] = False
    if state["active_position"]:
        await close_pos()
    log("🚨 دستور اضطراری (PANIC): تمام پوزیشن‌ها بسته و اتوپایلوت خاموش شد.")
    return {"status": "panic"}

@app.get("/api/export/csv")
async def export_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["زمان", "نوع", "قیمت ورود", "قیمت خروج", "سود/زیان"])
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for row in cursor.execute("SELECT time_str, side, entry_price, exit_price, pnl FROM trades ORDER BY id DESC"):
            w.writerow(row)
    return Response(content=out.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=trades_history.csv"})
