import time
import logging
import requests
from src.core.paper_live_runner import PaperTradingLiveRunner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("AtriaPaperNobitex")

session = requests.Session()
# تنظیم هدر واقعی جهت جلوگیری از بلاک شدن درخواست
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

def get_nobitex_market_data(symbol="btc-usdt"):
    """دریافت نرخ لحظه‌ای نوبیتکس با مقاومت در برابر خطاهای شبکه ایران"""
    urls = [
        f"https://api.nobitex.ir/market/stats?srcCurrency={symbol.split('-')[0]}&dstCurrency={symbol.split('-')[1]}",
        f"https://api.nobitex.ir/v2/trades/{symbol.replace('-', '')}"
    ]
    
    for url in urls:
        try:
            resp = session.get(url, timeout=7)
            if resp.status_code == 200:
                data = resp.json()
                if "stats" in data:
                    stats = data.get("stats", {}).get(symbol, {})
                    latest = stats.get("latest")
                    if latest:
                        return float(latest)
                elif "trades" in data and len(data["trades"]) > 0:
                    return float(data["trades"][0].get("price", 0))
        except Exception:
            continue
    return None

def main():
    print("=" * 65)
    print("🚀 AtriaTrade: Starting Live Paper Trading Session")
    print("🌐 Exchange Target: Nobitex (Resilient Mode)")
    print("💰 Initial Virtual Balance: 10,000 USDT")
    print("🛡️ Risk Engine: Market Regime Filter + Portfolio Risk Manager")
    print("=" * 65)

    symbol = "BTC/USDT"
    runner = PaperTradingLiveRunner(symbol=symbol, initial_balance=10000.0)
    runner.start()

    logger.info(f"🟢 Runner active for {symbol}. Fetching live ticks...")

    consecutive_fails = 0
    try:
        while runner.is_running:
            price = get_nobitex_market_data("btc-usdt")
            if price and price > 0:
                consecutive_fails = 0
                candle = {
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 1.0,
                    "timestamp": time.time()
                }
                res = runner.ingest_candle(candle)
                regime = res.get("regime", "UNKNOWN")
                bal = res.get("balance", runner.balance)
                logger.info(f"📊 {symbol} Price: {price:,.2f} | Regime: {regime} | Balance: {bal:,.2f} USDT")
            else:
                consecutive_fails += 1
                if consecutive_fails % 3 == 0:
                    logger.warning("⚠️ Network/DNS hiccup. Retrying connection...")
            
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n" + "=" * 65)
        print("🛑 Safely stopping Paper Trading Runner...")
        runner.stop()
        print(f"💼 Final Balance: {runner.balance:,.2f} USDT")
        print("✅ Session closed successfully.")
        print("=" * 65)

if __name__ == "__main__":
    main()
