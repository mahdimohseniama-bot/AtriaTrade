from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import time

app = FastAPI(title="AtriaTrade Pro Dashboard")

# وضعیت شبیه‌ساز امن Paper Trading
state = {
    "bot_status": "active",
    "mode": "paper_trading",
    "balance_usdt": 10000.0,
    "equity": 10250.0,
    "pnl_usd": 250.0,
    "pnl_pct": 2.5,
    "vault_balance": 50.0,
    "btc_price": 64250.0,
    "rsi": 54.2,
    "trades": [
        {"time": "10:45:12", "symbol": "BTC/USDT", "side": "BUY", "price": 63800.0, "profit": 22.5, "status": "CLOSED"},
        {"time": "10:30:45", "symbol": "BTC/USDT", "side": "SELL", "price": 64150.0, "profit": 35.0, "status": "CLOSED"},
        {"time": "10:15:20", "symbol": "BTC/USDT", "side": "BUY", "price": 63500.0, "profit": -12.0, "status": "CLOSED"},
        {"time": "09:50:11", "symbol": "BTC/USDT", "side": "BUY", "price": 63200.0, "profit": 45.0, "status": "CLOSED"}
    ],
    "logs": [
        "[10:55:00] [SYSTEM] سیستم Paper Trading با موتور شبیه‌ساز آماده است.",
        "[10:56:12] [RISK] صندوق Safe Vault فعال: ۲۰٪ از سود معاملات منتقل شد.",
        "[10:58:30] [ENGINE] پایش بازار فعال روی جفت‌ارز BTC/USDT با RSI=54.2",
        "[10:59:01] [TELEMETRY] وب‌سوکت وضعیت داشبورد بدون خطا پایدار است."
    ]
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATRIATRADE PRO</title>
    <style>
        :root {
            --bg: #090d16;
            --card-bg: #131a2a;
            --border: rgba(255, 255, 255, 0.08);
            --primary: #3b82f6;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
        body { background-color: var(--bg); color: var(--text-main); padding: 12px; font-size: 13px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 12px; }
        .brand { font-size: 18px; font-weight: 900; color: #60a5fa; letter-spacing: 0.5px; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid var(--success); }
        
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 12px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
        .card-title { font-size: 11px; color: var(--text-muted); }
        .card-value { font-size: 17px; font-weight: 800; }
        .card-sub { font-size: 11px; }
        
        .text-green { color: var(--success); }
        .text-red { color: var(--danger); }
        .text-yellow { color: var(--warning); }
        
        .panel { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
        .panel-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        
        .controls { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        button { border: none; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s; font-size: 12px; }
        .btn-start { background: #10b981; color: white; }
        .btn-pause { background: #f59e0b; color: white; }
        .btn-buy { background: #3b82f6; color: white; }
        .btn-panic { background: #ef4444; color: white; }
        
        .chart-box { height: 160px; width: 100%; position: relative; margin-top: 6px; }
        canvas { width: 100%; height: 100%; display: block; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 11px; text-align: center; }
        th, td { padding: 8px 4px; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); font-weight: 600; }
        
        .log-box { height: 110px; overflow-y: auto; font-family: monospace; font-size: 11px; background: rgba(0,0,0,0.35); padding: 8px 10px; border-radius: 6px; color: #cbd5e1; direction: ltr; text-align: left; line-height: 1.6; }
    </style>
</head>
<body>

    <div class="header">
        <div>
            <div class="brand">ATRIATRADE PRO</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">حالت Paper Trading / شبیه‌ساز امن</div>
        </div>
        <div class="badge" id="botBadge">فعال ●</div>
    </div>

    <!-- Stats Grid -->
    <div class="grid">
        <div class="card">
            <span class="card-title">کل ارزش (Equity)</span>
            <span class="card-value text-green" id="equity">$10,250.00</span>
            <span class="card-sub text-green" id="pnl">+250.00$ (+2.5%)</span>
        </div>
        <div class="card">
            <span class="card-title">موجودی کل (USDT)</span>
            <span class="card-value" id="balance">$10,000.00</span>
            <span class="card-sub text-muted">دارایی قابل استفاده</span>
        </div>
        <div class="card">
            <span class="card-title">قیمت لحظه‌ای BTC</span>
            <span class="card-value" id="btcPrice">$64,250.00</span>
            <span class="card-sub text-muted" id="rsi">RSI: 54.2</span>
        </div>
        <div class="card">
            <span class="card-title">صندوق امن (Safe Vault)</span>
            <span class="card-value text-yellow" id="vault">$50.00</span>
            <span class="card-sub text-muted">سود ذخیره‌شده</span>
        </div>
    </div>

    <!-- Controls -->
    <div class="panel">
        <div class="panel-title">فرمان‌های سریع ربات</div>
        <div class="controls">
            <button class="btn-start" onclick="botAction('start')">▶ شروع / ادامه ربات</button>
            <button class="btn-pause" onclick="botAction('stop')">⏸ توقف موقت ربات</button>
            <button class="btn-buy" onclick="botAction('quick_buy')">🛒 خرید آزمایشی (Paper)</button>
            <button class="btn-panic" onclick="botAction('panic')">🚨 خروج اضطراری (PANIC)</button>
        </div>
    </div>

    <!-- Live Chart -->
    <div class="panel">
        <div class="panel-title">
            <span>چارت قیمت زنده (BTC/USDT)</span>
            <span style="font-size: 10px; color: var(--text-muted);">تایم‌فریم ۱ دقیقه</span>
        </div>
        <div class="chart-box">
            <canvas id="liveChart"></canvas>
        </div>
    </div>

    <!-- Trades Table -->
    <div class="panel">
        <div class="panel-title">آخرین معاملات انجام‌شده</div>
        <table>
            <thead>
                <tr>
                    <th>زمان</th>
                    <th>جفت‌ارز</th>
                    <th>نوع</th>
                    <th>قیمت</th>
                    <th>سود (USDT)</th>
                    <th>وضعیت</th>
                </tr>
            </thead>
            <tbody id="tradesTable">
            </tbody>
        </table>
    </div>

    <!-- Live Logs -->
    <div class="panel">
        <div class="panel-title">لاگ‌های سیستمی زنده</div>
        <div class="log-box" id="logBox"></div>
    </div>

    <script>
        const canvas = document.getElementById('liveChart');
        const ctx = canvas.getContext('2d');
        let priceHistory = [64120, 64150, 64100, 64180, 64210, 64190, 64250];

        function drawChart() {
            const w = canvas.parentElement.clientWidth;
            const h = canvas.parentElement.clientHeight;
            canvas.width = w;
            canvas.height = h;

            ctx.clearRect(0, 0, w, h);
            const min = Math.min(...priceHistory) * 0.999;
            const max = Math.max(...priceHistory) * 1.001;

            // Grid lines
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            ctx.lineWidth = 1;
            for (let i = 1; i < 4; i++) {
                ctx.beginPath();
                ctx.moveTo(0, (h / 4) * i);
                ctx.lineTo(w, (h / 4) * i);
                ctx.stroke();
            }

            // Price path
            ctx.beginPath();
            ctx.strokeStyle = '#3b82f6';
            ctx.lineWidth = 2.5;

            priceHistory.forEach((p, i) => {
                const x = (i / (priceHistory.length - 1)) * w;
                const y = h - ((p - min) / (max - min)) * (h - 24) - 12;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // Gradient area
            ctx.lineTo(w, h);
            ctx.lineTo(0, h);
            const grad = ctx.createLinearGradient(0, 0, 0, h);
            grad.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
            grad.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
            ctx.fillStyle = grad;
            ctx.fill();
        }

        async function updateDashboard() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                // Values
                const bal = Number(data.balance_usdt || 10000);
                const eq = Number(data.equity || 10250);
                const pnl = Number(data.pnl_usd || 0);
                const pnlPct = Number(data.pnl_pct || 0);
                const vault = Number(data.vault_balance || 0);
                const btc = Number(data.btc_price || 64250);

                document.getElementById('balance').innerText = '$' + bal.toLocaleString(undefined, {minimumFractionDigits: 2});
                document.getElementById('equity').innerText = '$' + eq.toLocaleString(undefined, {minimumFractionDigits: 2});
                document.getElementById('pnl').innerText = (pnl >= 0 ? '+' : '') + pnl.toFixed(2) + '$ (' + (pnl >= 0 ? '+' : '') + pnlPct.toFixed(2) + '%)';
                document.getElementById('vault').innerText = '$' + vault.toFixed(2);
                document.getElementById('btcPrice').innerText = '$' + btc.toLocaleString(undefined, {minimumFractionDigits: 2});

                // Status Badge
                const isAct = data.bot_status === 'active';
                const badge = document.getElementById('botBadge');
                badge.innerText = isAct ? 'فعال ●' : 'متوقف ⏸';
                badge.style.color = isAct ? 'var(--success)' : 'var(--warning)';
                badge.style.borderColor = isAct ? 'var(--success)' : 'var(--warning)';

                // Trades Table
                if (data.trades && data.trades.length) {
                    const tbody = document.getElementById('tradesTable');
                    tbody.innerHTML = data.trades.map(t => `
                        <tr>
                            <td style="color:var(--text-muted);">${t.time}</td>
                            <td style="font-weight:700;">${t.symbol}</td>
                            <td style="color:${t.side === 'BUY' ? 'var(--success)' : 'var(--danger)'}; font-weight:700;">${t.side}</td>
                            <td>$${Number(t.price).toLocaleString()}</td>
                            <td class="${t.profit >= 0 ? 'text-green' : 'text-red'}" style="font-weight:700;">
                                ${t.profit >= 0 ? '+' : ''}${Number(t.profit).toFixed(1)}$
                            </td>
                            <td><span style="font-size:10px; padding:2px 6px; border-radius:4px; background:rgba(255,255,255,0.06);">${t.status}</span></td>
                        </tr>
                    `).join('');
                }

                // Logs Box
                if (data.logs && data.logs.length) {
                    const logBox = document.getElementById('logBox');
                    logBox.innerHTML = data.logs.map(l => `<div>${l}</div>`).join('');
                    logBox.scrollTop = logBox.scrollHeight;
                }

                // Push new simulated tick for chart
                const noise = (Math.random() - 0.49) * 20;
                const nextP = Math.round(priceHistory[priceHistory.length - 1] + noise);
                priceHistory.push(nextP);
                if (priceHistory.length > 25) priceHistory.shift();
                drawChart();

            } catch (err) {
                console.error("Fetch status error:", err);
            }
        }

        async function botAction(action) {
            let endpoint = '/api/bot/start';
            if (action === 'stop' || action === 'panic') endpoint = '/api/bot/stop';
            if (action === 'quick_buy') endpoint = '/api/bot/quick_buy';
            await fetch(endpoint, { method: 'POST' });
            updateDashboard();
        }

        window.addEventListener('resize', drawChart);
        drawChart();
        updateDashboard();
        setInterval(updateDashboard, 2500);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/status")
@app.get("/api/telemetry")
async def get_status():
    return JSONResponse(state)

@app.post("/api/bot/start")
async def start_bot():
    state["bot_status"] = "active"
    state["logs"].append(f"[{time.strftime('%H:%M:%S')}] [COMMAND] بات توسط کاربر فعال شد.")
    return JSONResponse({"status": "started", "bot_status": "active"})

@app.post("/api/bot/stop")
async def stop_bot():
    state["bot_status"] = "paused"
    state["logs"].append(f"[{time.strftime('%H:%M:%S')}] [COMMAND] بات توسط کاربر متوقف شد.")
    return JSONResponse({"status": "paused", "bot_status": "paused"})

@app.post("/api/bot/quick_buy")
async def quick_buy():
    cur_p = state["btc_price"]
    state["trades"].insert(0, {
        "time": time.strftime("%H:%M:%S"),
        "symbol": "BTC/USDT",
        "side": "BUY",
        "price": cur_p,
        "profit": 0.0,
        "status": "OPEN"
    })
    state["logs"].append(f"[{time.strftime('%H:%M:%S')}] [TRADE] سفارش خرید آزمایشی ثبت شد: 0.05 BTC در ${cur_p}")
    return JSONResponse({"status": "success"})
