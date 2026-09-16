// AtriaTrade Cyberpunk Live Dashboard JS
console.log("🔥 AtriaTrade Dashboard JS Loaded!");

let priceChart = null;
let priceHistory = [];
let timeLabels = [];

function initChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    // اگر چارت قبلاً ساخته شده بود، destroy کن
    if (priceChart) {
        priceChart.destroy();
    }

    priceChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'BTC/USDT',
                data: priceHistory,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 1,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#94a3b8',
                    bodyColor: '#f8fafc',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', maxTicksLimit: 6 }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#64748b',
                        callback: function(value) { return '$' + value.toLocaleString(); }
                    }
                }
            }
        }
    });
}

function updateElement(id, value, className = null) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
        if (className) el.className = className;
    }
}

async function fetchTelemetry() {
    try {
        const response = await fetch('/api/telemetry', {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            credentials: 'include'
        });

        if (response.status === 401) {
            console.warn("⚠️ Unauthorized (401) - Redirecting to login...");
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            console.error("❌ Telemetry fetch error:", response.status);
            return;
        }

        const data = await response.json();
        renderDashboard(data);
    } catch (err) {
        console.error("❌ Telemetry Network Exception:", err);
    }
}

function renderDashboard(data) {
    if (!data) return;

    // ۱. متغیرهای مالی و سیستمی
    const btcPrice = parseFloat(data.btc_price || data.price || 0);
    const equity = parseFloat(data.equity || data.balance || 0);
    const safeProfit = parseFloat(data.safe_profit || data.profit_reserve || 0);
    const winRate = parseFloat(data.win_rate || 0);
    const totalPnl = parseFloat(data.total_pnl || data.pnl || 0);
    const rsi = parseFloat(data.rsi || 0);
    const trend = data.trend || data.market_trend || 'NEUTRAL';
    const status = data.bot_status || (data.is_running ? 'RUNNING' : 'STOPPED');

    // ۲. به‌روزرسانی کارت‌ها در صفحه
    updateElement('btc-price', btcPrice > 0 ? `$${btcPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '--');
    updateElement('account-equity', `$${equity.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    updateElement('safe-profit', `$${safeProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    updateElement('win-rate', `${winRate.toFixed(1)}% (${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)})`);

    // ۳. تحلیل تکنیکال (RSI و روند)
    updateElement('rsi-val', rsi > 0 ? rsi.toFixed(1) : '--');
    
    let trendFa = 'خنثی';
    let trendClass = 'text-gray-400 font-bold';
    if (trend.toUpperCase().includes('BULL') || trend.toUpperCase().includes('صعودی')) {
        trendFa = 'صعودی 🟢';
        trendClass = 'text-emerald-400 font-bold';
    } else if (trend.toUpperCase().includes('BEAR') || trend.toUpperCase().includes('نزولی')) {
        trendFa = 'نزولی 🔴';
        trendClass = 'text-rose-400 font-bold';
    }
    updateElement('trend-val', trendFa, trendClass);

    // ۴. وضعیت اتوپایلوت
    const statusPill = document.getElementById('autopilot-status');
    if (statusPill) {
        if (status === 'RUNNING' || data.is_running) {
            statusPill.textContent = 'اتوپایلوت: فعال';
            statusPill.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        } else {
            statusPill.textContent = 'اتوپایلوت: متوقف';
            statusPill.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30';
        }
    }

    // ۵. به‌روزرسانی پوزیشن فعال
    const pos = data.position;
    if (pos && pos.side && pos.side !== 'NONE') {
        const sideFa = pos.side === 'BUY' || pos.side === 'LONG' ? 'خرید (Long)' : 'فروش (Short)';
        const pnl = parseFloat(pos.unrealized_pnl || 0);
        updateElement('pos-status', `${sideFa} - حجم: ${pos.size || '0.02'} BTC`);
        updateElement('pos-pnl', `PnL: ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`, pnl >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold');
    } else {
        updateElement('pos-status', 'بدون معامله باز');
        updateElement('pos-pnl', 'PnL: $0.00', 'text-gray-400');
    }

    // ۶. به‌روزرسانی چارت
    if (btcPrice > 0) {
        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
        
        if (priceHistory.length === 0 || priceHistory[priceHistory.length - 1] !== btcPrice) {
            timeLabels.push(timeStr);
            priceHistory.push(btcPrice);
            
            if (priceHistory.length > 30) {
                priceHistory.shift();
                timeLabels.shift();
            }

            if (priceChart) {
                priceChart.update();
            }
        }
    }

    // ۷. زمان آخرین آپدیت
    const now = new Date();
    updateElement('last-update', `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`);
}

// حلقه مانیتورینگ منظم
async function telemetryLoop() {
    await fetchTelemetry();
    setTimeout(telemetryLoop, 2000);
}

// راه‌اندازی پس از بارگذاری DOM
window.addEventListener('load', () => {
    console.log("⚡ Dashboard ready, starting chart & polling...");
    initChart();
    telemetryLoop();
});
