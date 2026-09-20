import time
import requests
from datetime import datetime
from src.adapters.paper_factory import PaperExchangeFactory
from src.core.market_regime import MarketRegimeFilter
from src.core.portfolio_risk import PortfolioRiskManager
from src.core.paper_live_runner import PaperTradingLiveRunner

def fetch_wallex_live_price(symbol="BTCUSDT"):
    url = "https://api.wallex.ir/v1/markets"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            symbols_data = data.get("result", {}).get("symbols", {})
            if symbol in symbols_data:
                stats = symbols_data[symbol].get("stats", {})
                return float(stats.get("lastPrice", 0.0))
    except Exception as e:
        print(f"⚠️ [API Warning]: {e}")
    return None

def main():
    print("\n" + "="*68)
    print("⚡ [AtriaTrade] Wallex Forward-Testing with Auto-Execution")
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*68)

    symbol = "BTCUSDT"

    # ۱. راه‌اندازی آداپتور و لایه‌های ریسک و رژیم
    adapter = PaperExchangeFactory.create_adapter(
        "wallex",
        initial_balances={"tm": 100_000_000.0, "usdt": 2_000.0, "btc": 0.05}
    )

    regime_filter = MarketRegimeFilter(fast_window=3, slow_window=5)
    risk_manager = PortfolioRiskManager(max_total_exposure_pct=0.8, max_open_positions=2)

    runner = PaperTradingLiveRunner(
        symbol=symbol,
        initial_balance=2_000.0,
        regime_filter=regime_filter,
        portfolio_risk=risk_manager
    )
    runner.start()

    print("🎯 Engines initialized. Ingesting live ticks & executing strategies...")
    print("-" * 68)

    history_candles = []

    for i in range(1, 16):
        live_price = fetch_wallex_live_price(symbol)
        if not live_price or live_price <= 0:
            live_price = 80600.0 + (i * 12.0)

        adapter.set_market_price(symbol, live_price)

        candle = {
            "symbol": symbol,
            "open": history_candles[-1]["close"] if history_candles else live_price - 5.0,
            "high": live_price + 20.0,
            "low": live_price - 20.0,
            "close": live_price,
            "volume": 2.1,
            "timestamp": time.time()
        }
        history_candles.append(candle)

        # ۱. پردازش کندل و تشخیص رژیم بازار
        res = runner.ingest_candle(candle)
        regime = res.get("regime", "UNKNOWN")

        # ۲. شبیه‌سازی ورود/خروج پیپر متصل به پایپ‌لاین
        action_note = "SCANNING"
        if regime in ["RANGING", "TRENDING"] and len(runner.open_positions) == 0 and i == 6:
            trade_res = runner.process_signal({
                "side": "BUY",
                "amount": 500.0,
                "stop_loss": live_price * 0.99,
                "take_profit": live_price * 1.015
            }, candle)
            action_note = f"🟢 BUY ({trade_res.get('status', 'EXECUTED')})"
        elif len(runner.open_positions) > 0 and i >= 12:
            trade_res = runner.process_signal({
                "side": "SELL"
            }, candle)
            pnl = trade_res.get("pnl", 0.0)
            action_note = f"🔴 CLOSE (PnL: ${pnl:+.2f})"

        open_pos_count = len(runner.open_positions)
        print(f"[{i:02d}/15] 💰 ${live_price:,.2f} | 🧭 {regime:<8} | 🎯 {action_note:<22} | 📦 Pos: {open_pos_count} | 💵 ${runner.balance:,.2f}")
        time.sleep(2)

    print("\n" + "="*68)
    print("🏁 Forward-Test Session Complete:")
    print(f"   Runner Capital: ${runner.balance:,.2f}")
    print(f"   Closed Trades: {len(runner.trade_history)}")
    if runner.trade_history:
        for idx, trade in enumerate(runner.trade_history, 1):
            print(f"   Trade #{idx}: Exit @ ${trade.get('exit_price', 0):,.2f} | PnL: ${trade.get('pnl', 0.0):+.2f}")
    print("="*68)

if __name__ == "__main__":
    main()
