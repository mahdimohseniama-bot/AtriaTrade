import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.core.engine import TradingEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

app = FastAPI(title="AtriaTrade Dashboard")

# تعریف نمونه موتور ترید
engine = TradingEngine(initial_balance=1000.0, symbol="BTC/USDT")
bot_running = True
latest_ticks = []

async def trading_background_task():
    """حلقه پس‌زمینه برای اجرای تیک‌های موتور ترید هر 3 ثانیه"""
    global bot_running, latest_ticks
    while True:
        if bot_running:
            try:
                tick_data = engine.execute_tick()
                latest_ticks.append(tick_data)
                if len(latest_ticks) > 20:
                    latest_ticks.pop(0)
            except Exception as e:
                logging.error(f"Error in trading loop: {e}")
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_background_task())

@app.get("/api/status")
async def get_status():
    """ارسال وضعیت لحظه‌ای به داشبورد"""
    return {
        "running": bot_running,
        "symbol": engine.symbol,
        "balance": round(engine.balance, 2),
        "position": round(engine.position, 6),
        "entry_price": engine.entry_price,
        "history": latest_ticks[-10:]
    }

@app.post("/api/toggle")
async def toggle_bot():
    global bot_running
    bot_running = not bot_running
    return {"running": bot_running}

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AtriaTrade Pro Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
            .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; }
            .badge-buy { background-color: #10b981; }
            .badge-sell { background-color: #ef4444; }
            .badge-hold { background-color: #64748b; }
            .log-box { background: #020617; border: 1px solid #1e293b; height: 260px; overflow-y: auto; font-family: monospace; font-size: 0.85rem; }
        </style>
    </head>
    <body class="p-3">
        <div class="container-fluid max-w-lg">
            <header class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="m-0 text-info">⚡ AtriaTrade <small class="text-secondary fs-6">Paper Engine</small></h4>
                <button id="toggle-btn" class="btn btn-sm btn-success" onclick="toggleBot()">وضعیت: فعال</button>
            </header>

            <div class="row g-2 mb-3">
                <div class="col-6">
                    <div class="card p-2 text-center">
                        <small class="text-secondary">موجودی (USDT)</small>
                        <h4 id="balance" class="text-success m-0">$1000.00</h4>
                    </div>
                </div>
                <div class="col-6">
                    <div class="card p-2 text-center">
                        <small class="text-secondary">پوزیشن BTC</small>
                        <h4 id="position" class="text-warning m-0">0.000000</h4>
                    </div>
                </div>
            </div>

            <div class="card p-3 mb-3">
                <h6 class="text-light mb-2">📜 گزارش زنده معاملات و سیگنال‌ها</h6>
                <div id="logs" class="log-box p-2 rounded">در حال دریافت اطلاعات...</div>
            </div>
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    
                    document.getElementById('balance').innerText = '$' + data.balance.toFixed(2);
                    document.getElementById('position').innerText = data.position.toFixed(6);
                    
                    const btn = document.getElementById('toggle-btn');
                    btn.className = data.running ? 'btn btn-sm btn-success' : 'btn btn-sm btn-danger';
                    btn.innerText = data.running ? 'وضعیت: فعال' : 'وضعیت: متوقف';

                    let logsHtml = '';
                    data.history.slice().reverse().forEach(t => {
                        let badgeClass = t.signal === 'BUY' ? 'badge-buy' : (t.signal === 'SELL' ? 'badge-sell' : 'badge-hold');
                        logsHtml += `<div class="mb-1 border-bottom border-dark pb-1">
                            <span class="badge ${badgeClass}">${t.signal}</span> 
                            <span>${t.symbol} @ $${t.price.toFixed(2)}</span> - 
                            <span class="text-info">${t.action}</span>
                        </div>`;
                    });
                    if (logsHtml) document.getElementById('logs').innerHTML = logsHtml;
                } catch(e) { console.error(e); }
            }

            async function toggleBot() {
                await fetch('/api/toggle', {method: 'POST'});
                updateDashboard();
            }

            setInterval(updateDashboard, 2000);
            updateDashboard();
        </script>
    </body>
    </html>
    """
