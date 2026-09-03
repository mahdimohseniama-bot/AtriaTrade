import os

code = '''import asyncio
import random
import time
import sqlite3
import csv
import io
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

DB_PATH = "atriatrade.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY,
                equity REAL,
                safe_profit REAL,
                autopilot INTEGER,
                updated_at REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                side TEXT,
                amount REAL,
                entry_price REAL,
                exit_price REAL,
                pnl REAL,
                pnl_percent REAL,
                closed_at REAL,
                reason TEXT
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM state WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO state (id, equity, safe_profit, autopilot, updated_at) VALUES (1, 10000.0, 0.0, 1, ?)",
                (time.time(),)
            )
        conn.commit()

init_db()

def load_state():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT equity, safe_profit, autopilot FROM state WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {"equity": row[0], "safe_profit": row[1], "autopilot": bool(row[2])}
        return {"equity": 10000.0, "safe_profit": 0.0, "autopilot": True}

def save_state(equity: float, safe_profit: float, autopilot: bool):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE state SET equity = ?, safe_profit = ?, autopilot = ?, updated_at = ? WHERE id = 1",
            (equity, safe_profit, 1 if autopilot else 0, time.time())
        )
        conn.commit()

def record_trade_db(trade: dict):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (symbol, side, amount, entry_price, exit_price, pnl, pnl_percent, closed_at, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.get("symbol", "BTC/USDT"),
            trade.get("side", "BUY"),
            trade.get("amount", 0.02),
            trade.get("entry_price", 0.0),
            trade.get("exit_price", 0.0),
            trade.get("pnl", 0.0),
            trade.get("pnl_percent", 0.0),
            trade.get("closed_at", time.time()),
            trade.get("reason", "AUTO_CLOSE")
        ))
        conn.commit()

def fetch_recent_trades(limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, side, amount, entry_price, exit_price, pnl, pnl_percent, closed_at, reason
            FROM trades ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        trades = []
        for r in rows:
            trades.append({
                "symbol": r[0],
                "side": r[1],
                "amount": r[2],
                "entry_price": r[3],
                "exit_price": r[4],
                "pnl": r[5],
                "pnl_percent": r[6],
                "closed_at": r[7],
                "time_str": time.strftime("%H:%M:%S", time.localtime(r[7])),
                "reason": r[8]
            })
        return trades

app = FastAPI(title="AtriaTrade Paper Trading Engine", version="0.2.0")

initial_db_state = load_state()

engine_state = {
    "equity": initial_db_state["equity"],
    "safe_profit": initial_db_state["safe_profit"],
    "autopilot": initial_db_state["autopilot"],
    "active_position": None,
    "current_price": 63350.0,
    "rsi": 50.0,
    "trend": "NEUTRAL",
    "win_rate": 0.0,
    "total_profit": 0.0,
    "price_history": [63350.0] * 30,
    "logs": ["[AtriaTrade Engine v0.2.0 Online]"]
}

def log_event(msg: str):
    ts = time.strftime("%H:%M:%S")
    engine_state["logs"].append(f"[{ts}] {msg}")
    if len(engine_state["logs"]) > 40:
        engine_state["logs"].pop(0)

def open_position(side: str, amount: float, reason: str):
    if engine_state["active_position"]:
        return False
    price = engine_state["current_price"]
    engine_state["active_position"] = {
        "symbol": "BTC/USDT",
        "side": side,
        "amount": amount,
        "entry_price": price,
        "opened_at": time.time(),
        "pnl": 0.0,
        "pnl_pct": 0.0
    }
    log_event(f"Position {side} opened at ${price:,.2f} ({reason})")
    return True

def close_position(reason: str):
    pos = engine_state["active_position"]
    if not pos:
        return False
    exit_price = engine_state["current_price"]
    pnl = pos["pnl"]
    pnl_pct = pos["pnl_pct"]
    
    engine_state["equity"] = round(engine_state["equity"] + pnl, 2)
    
    if pnl > 0:
        vault_cut = round(pnl * 0.20, 2)
        engine_state["safe_profit"] = round(engine_state["safe_profit"] + vault_cut, 2)
        log_event(f"Safe Vault +${vault_cut} (20% profit reserved)")
        
    engine_state["total_profit"] = round(engine_state["total_profit"] + pnl, 2)
    
    trade_record = {
        "symbol": pos["symbol"],
        "side": pos["side"],
        "amount": pos["amount"],
        "entry_price": pos["entry_price"],
        "exit_price": exit_price,
        "pnl": pnl,
        "pnl_percent": pnl_pct,
        "closed_at": time.time(),
        "reason": reason
    }
    record_trade_db(trade_record)
    save_state(engine_state["equity"], engine_state["safe_profit"], engine_state["autopilot"])
    
    engine_state["active_position"] = None
    log_event(f"Position closed ({reason}) | PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    return True

async def market_simulator_and_autopilot():
    prices = list(engine_state["price_history"])
    while True:
        await asyncio.sleep(1.5)
        shock = random.gauss(0, 35.0)
        new_price = max(1000.0, round(prices[-1] + shock, 2))
        prices.append(new_price)
        if len(prices) > 40:
            prices.pop(0)
            
        engine_state["current_price"] = new_price
        engine_state["price_history"] = prices[-30:]
        
        if len(prices) >= 15:
            gains, losses = [], []
            for i in range(len(prices)-14, len(prices)):
                diff = prices[i] - prices[i-1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(diff))
            avg_gain = sum(gains) / 14.0
            avg_loss = sum(losses) / 14.0
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = round(100.0 - (100.0 / (1.0 + rs)), 2)
            engine_state["rsi"] = rsi
            
            if rsi > 60:
                engine_state["trend"] = "BULLISH"
            elif rsi < 40:
                engine_state["trend"] = "BEARISH"
            else:
                engine_state["trend"] = "NEUTRAL"
                
        pos = engine_state["active_position"]
        if pos:
            entry = pos["entry_price"]
            amt = pos["amount"]
            if pos["side"] == "BUY":
                pnl = (new_price - entry) * amt
            else:
                pnl = (entry - new_price) * amt
            pos["pnl"] = round(pnl, 2)
            pos["pnl_pct"] = round((pnl / (entry * amt)) * 100, 2)
            
            if engine_state["autopilot"]:
                if pos["pnl_pct"] >= 1.5:
                    close_position("Take Profit (Target reached)")
                elif pos["pnl_pct"] <= -1.0:
                    close_position("Stop Loss (Risk protection)")
        else:
            if engine_state["autopilot"]:
                rsi = engine_state["rsi"]
                if rsi < 30:
                    open_position("BUY", 0.02, "Auto RSI Oversold")
                elif rsi > 70:
                    open_position("SELL", 0.02, "Auto RSI Overbought")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_simulator_and_autopilot())

@app.get("/api/telemetry")
def get_telemetry():
    trades = fetch_recent_trades(5)
    return {
        "current_price": engine_state["current_price"],
        "rsi": engine_state["rsi"],
        "trend": engine_state["trend"],
        "equity": engine_state["equity"],
        "safe_profit": engine_state["safe_profit"],
        "autopilot": engine_state["autopilot"],
        "total_profit": engine_state["total_profit"],
        "active_position": engine_state["active_position"],
        "price_history": engine_state["price_history"],
        "recent_trades": trades,
        "logs": engine_state["logs"][-12:]
    }

@app.post("/api/order/manual")
def manual_order(payload: dict):
    side = payload.get("side", "BUY")
    amount = float(payload.get("amount", 0.02))
    success = open_position(side, amount, "Manual User Order")
    return {"status": "ok" if success else "failed"}

@app.post("/api/order/close")
def manual_close():
    if not engine_state["active_position"]:
        raise HTTPException(status_code=400, detail="No active position")
    success = close_position("Manual User Close")
    return {"status": "ok" if success else "failed"}

@app.post("/api/autopilot/toggle")
def toggle_autopilot():
    engine_state["autopilot"] = not engine_state["autopilot"]
    save_state(engine_state["equity"], engine_state["safe_profit"], engine_state["autopilot"])
    st = "ACTIVE" if engine_state["autopilot"] else "DISABLED"
    log_event(f"Autopilot switched to {st}")
    return {"autopilot": engine_state["autopilot"]}

@app.post("/api/panic")
def panic_button():
    engine_state["autopilot"] = False
    if engine_state["active_position"]:
        close_position("PANIC_STOP")
    save_state(engine_state["equity"], engine_state["safe_profit"], engine_state["autopilot"])
    log_event("EMERGENCY PANIC TRIGGERED")
    return {"status": "panic_activated"}

@app.get("/api/export/csv")
def export_csv():
    trades = fetch_recent_trades(200)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(def manual_close():
    if not engine_state["active_position"]:
        raise HTTPException(status_code=400, detail="No active position")
    success = close_position("Manual User Close")
    return {"status": "ok" if success else "failed"}

@app.post("/api/autopilot/toggle")
def toggle_autopilot():
    engine_state["autopilot"] = not engine_state["autopilot"]
    save_state(engine_state["equity"], engine_state["safe_profit"], engine_state["autopilot"])
    st = "ACTIVE" if engine_state["autopilot"] else "DISABLED"
    log_event(f"Autopilot switched to {st}")
    return {"autopilot": engine_state["autopilot"]}

@app.post("/api/panic")
def panic_button():
    engine_state["autopilot"] = False
    if engine_state["active_position"]:
        close_position("PANIC_STOP")
    save_state(engine_state["equity"], engine_state["safe_profit"], engine_state["autopilot"])
    log_event("EMERGENCY PANIC TRIGGERED")
    return {"status": "panic_activated"}

@app.get("/api/export/csv")
def export_csv():
    trades = fetch_recent_trades(200)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Symbol", "Side", "Amount", "Entry Price", "Exit Price", "PnL ($)", "PnL (%)", "Time", "Reason"])
    for idx, t in enumerate(trades, 1):
        writer.writerow([idx, t["symbol"], t["side"], t["amount"], t["entry_price"], t["exit_price"], t["pnl"], t["pnl_percent"], t["time_str"], t["reason"]])
    output.seek(0)
    return StreamingResponse(
        iter(btns { display: flex; gap: 8px; }
        .btn { border: none; border-radius: 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer; padding: 8px 12px; transition: 0.2s; }
        .btn-panic { background: #ef4444; color: white; }
        .btn-auto-on { background: #10b981; color: white; }
        .btn-auto-off { background: #4b5563; color: white; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
        .card { background: #151c2e; border: 1px solid #1f293d; border-radius: 12px; padding: 12px; }
        .card-title { font-size: 0.75rem; color: #9ca3af; margin-bottom: 4px; }
        .card-value { font-size: 1.1rem; font-weight: 700; }
        .chart-container { background: #151c2e; border: 1px solid #1f293d; border-radius: 12px; padding: 12px; height: 190px; margin-bottom: 12px; }
        .pos-card { background: #151c2e; border: 1px solid #1f293d; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
        .pos-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.85rem; }
        .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
        .btn-buy { background: #10b981; color: white; padding: 12px; }
        .btn-sell { background: #ef4444; color: white; padding: 12px; }
        .btn-close { background: #eab308; color: black; grid-column: span 2; padding: 10px; }
        .table-card { background: #151c2e; border: 1px solid #1f293d; border-radius: 12px; padding: 12px; margin-bottom: 12px; }
        .table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.85rem; font-weight: 700; color: #38bdf8; }
        table { width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: right; }
        th, td { padding: 6px 4px; border-bottom: 1px solid #1f293d; }
        th { color: #9ca3af; font-weight: 600; }
        .logs-card { background: #070a10; border: 1px solid #1f293d; border-radius: 12px; padding: 10px; font-family: monospace; font-size: 0.72rem; color: #10b981; height: 110px; overflow-y: auto; }
        .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
        .badge-buy { background: #064e3b; color: #34d399; }
        .badge-sell { background: #7f1d1d; color: #f87171; }
    </style>
</head>
<body>
    <div class="header">
        <h1><span>⚡</span> ATRATRADE PRO</h1>
        <div class="header-btns">
            <button id="btnPanic" class="btn btn-panic" onclick="triggerPanic()">PANIC</button>
            <button id="btnAuto" class="btn btn-auto-on" onclick="toggleAuto()">اتوپایلوت: فعال</button>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="card-title">قیمت BTC/USDT</div>
            <div class="card-value" id="priceDisplay">$0.00</div>
        </div>
        <div class="card">
            <div class="card-title">کل سرمایه (Equity)</div>
            <div class="card-value" id="equityDisplay" style="color:#38bdf8;">$10,000.00</div>
        </div>
        <div class="card">
            <div class="card-title">صندوق امن سود (Safe Vault)</div>
            <div class="card-value" id="vaultDisplay" style="color:#fbfb24;">$0.00</div>
        </div>
        <div class="card">
            <div class="card-title">RSI (14) / روند</div>
            <div class="card-value" id="rsiDisplay">50.0 / NEUTRAL</div>
        </div>
    </div>
    <div class="chart-container">
        <canvas id="priceChart"></canvas>
    </div>
    <div class="pos-card" id="posBox">
        <div class="pos-header">
            <strong>پوزیشن فعال:</strong>
            <span id="posStatus" style="color:#9ca3af;">بدون معامله باز</span>
        </div>
        <div id="posDetails" style="font-size:0.85rem; color:#d1d5db; display:none;">
            <div>حجم: 0.02 BTC | ورود: <span id="posEntry">$0</span></div>
            <div style="margin-top:4px; font-weight:bold;">سود/زیان: <span id="posPnL">$0.00 (0.00%)</span></div>
        </div>
    </div>
    <div class="action-grid">
        <button class="btn btn-buy" onclick="placeOrder('BUY')">خرید دستی (0.02 BTC)</button>
        <button class="btn btn-sell" onclick="placeOrder('SELL')">فروش دستی (0.02 BTC)</button>
        <button class="btn btn-close" id="btnClosePos" style="display:none;" onclick="closeActivePos()">بستن فوری پوزیشن</button>
    </div>
    <div class="table-card">
        <div class="table-header">
            <span>تاریخچه معاملات (SQLite)</span>
            <a href="/api/export/csv" style="color:#38bdf8; text-decoration:none; font-size:0.75rem;">دانلود CSV</a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>زمان</th>
                    <th>نوع</th>
                    <th>ورود</th>
                    <th>خروج</th>
                    <th>سود/زیان</th>
                </tr>
            </thead>
            <tbody id="tradeTableBody">
                <tr><td colspan="5" style="text-align:center; color:#6b7280;">هنوز معامله ای ثبت نشده است</td></tr>
            </tbody>
        </table>
    </div>
    <div class="logs-card" id="logBox"></div>
    <script>
        const ctx = document.getElementById("priceChart").getContext("2d");
        const chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: Array(30).fill(""),
                datasets: [{
                    data: Array(30).fill(63350),
                    borderColor: "#10b981",
                    borderWidth: 2,
                    fill: false,
                    tension: 0.2,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { grid: { color: "#1f293d" }, ticks: { color: "#9ca3af", font: { size: 10 } } }
                }
            }
        });

        async function updateTelemetry() {
            try {
                const res = await fetch("/api/telemetry");
                const data = await res.json();
                document.getElementById("priceDisplay").innerText = "$" + data.current_price.toLocaleString();
                document.getElementById("equityDisplay").innerText = "$" + data.equity.toLocaleString(undefined, {minimumFractionDigits:2});
                document.getElementById("vaultDisplay").innerText = "$" + data.safe_profit.toLocaleString(undefined, {minimumFractionDigits:2});
                document.getElementById("rsiDisplay").innerText = data.rsi + " (" + data.trend + ")";
                
                const btnAuto = document.getElementById("btnAuto");
                if (data.autopilot) {
                    btnAuto.className = "btn btn-auto-on";
                    btnAuto.innerText = "اتوپایلوت: فعال";
                } else {
                    btnAuto.className = "btn btn-auto-off";
                    btnAuto.innerText = "اتوپایلوت: غیرفعال";
                }

                chart.data.datasets[0].data = data.price_history;
                chart.update("none");

                const pos = data.active_position;
                const posDetails = document.getElementById("posDetails");
                const posStatus = document.getElementById("posStatus");
                const btnClose = document.getElementById("btnClosePos");
                if (pos) {
                    posStatus.innerHTML = '<span class="badge ' + (pos.side === 'BUY' ? 'badge-buy' : 'badge-sell') + '">' + pos.side + '</span>';
                    document.getElementById("posEntry").innerText = "$" + pos.entry_price.toLocaleString();
                    const pnlEl = document.getElementById("posPnL");
                    pnlEl.innerText = (pos.pnl >= 0 ? '+' : '') + '$' + pos.pnl + ' (' + (pos.pnl_pct >= 0 ? '+' : '') + pos.pnl_pct + '%)';
                    pnlEl.style.color = pos.pnl >= 0 ? "#34d399" : "#f87171";
                    posDetails.style.display = "block";
                    btnClose.style.display = "block";
                } else {
                    posStatus.innerText = "بدون معامله باز";
                    posDetails.style.display = "none";
                    btnClose.style.display = "none";
                }

                const tbody = document.getElementById("tradeTableBody");
                if (data.recent_trades && data.recent_trades.length > 0) {
                    tbody.innerHTML = data.recent_trades.map(t => '<tr><td>' + t.time_str + '</td><td><span class="badge ' + (t.side === 'BUY' ? 'badge-buy' : 'badge-sell') + '">' + t.side + '</span></td><td>$' + t.entry_price.toLocaleString() + '</td><td>$' + t.exit_price.toLocaleString() + '</td><td style="color:' + (t.pnl >= 0 ? '#34d399' : '#f87171') + '; font-weight:bold;">' + (t.pnl >= 0 ? '+' : '') + '$' + t.pnl + '</td></tr>').join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#6b7280;">هنوز معامله ای بسته نشده است.</td></tr>';
                }

                const logBox = document.getElementById("logBox");
                logBox.innerHTML = data.logs.join("<br>");
                logBox.scrollTop = logBox.scrollHeight;
            } catch (err) {
                console.error("Telemetry error:", err);
            }
        }

        async function placeOrder(side) {
            await fetch("/api/order/manual", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ side: side, amount: 0.02 })
            });
            updateTelemetry();
        }

        async function closeActivePos() {
            await fetch("/api/order/close", { method: "POST" });
            updateTelemetry();
        }

        async function toggleAuto() {
            await fetch("/api/autopilot/toggle", { method: "POST" });
            updateTelemetry();
        }

        async function triggerPanic() {
            if (confirm("آیا مطمئن هستید؟ ربات متوقف و پوزیشن بسته خواهد شد.")) {
                await fetch("/api/panic", { method: "POST" });
                updateTelemetry();
            }
        }

        setInterval(updateTelemetry, 1500);
        updateTelemetry();
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTML_DOC
'''

os.makedirs('src/web', exist_ok=True)
with open('src/web/app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("SUCCESS_FILE_CREATED")
