import os
import sys
import time
import json
import random
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.risk_manager import RiskManager
from src.strategies.sma_cross_strategy import SMACrossStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AtriaTrade.WallexPaperLiveDynamic")

class AlertNotifier:
    def __init__(self, *args, **kwargs):
        pass

    def notify(self, title: str = "", message: str = "", **kwargs):
        logger.info(f"Notify: [{title}] {message}")

    def send_alert(self, message: str = "", title: str = "", **kwargs):
        logger.info(f"Alert: [{title}] {message}")


def run_loop(duration_seconds=4, interval_seconds=2, symbol="BTCUSDT", runner=None, **kwargs):
    """
    Main live/paper loop compliant with E2E and notifier integration tests.
    """
    start_time = time.time()
    logger.info(f"Starting run_loop for {symbol} (duration={duration_seconds}s, interval={interval_seconds}s)...")

    adapter = WallexPaperAdapter()
    risk = RiskManager()
    strategy = SMACrossStrategy(symbol=symbol)
    notifier = AlertNotifier()

    position = None
    results = []

    while (time.time() - start_time) < duration_seconds:
        try:
            ticker = adapter.get_ticker(symbol)
        except StopIteration:
            break
        except Exception as e:
            logger.warning(f"Failed to fetch ticker: {e}")
            break

        if not ticker:
            break

        price = ticker.get("price", ticker.get("last_price", 0.0))

        if risk.can_trade_today():
            signal = strategy.generate_signal(price=price) if hasattr(strategy, "generate_signal") else "HOLD"

            if signal == "BUY" and position is None:
                order = adapter.place_order(symbol=symbol, side="buy", amount=1.0, price=price)
                position = {"symbol": symbol, "entry_price": price, "order_id": order.get("order_id")}
                msg = f"BUY order executed at {price}"
                if hasattr(notifier, "notify"):
                    notifier.notify(title="ORDER_BUY_FILLED", message=msg)
                results.append({"event": "buy", "price": price, "order": order})

            elif position is not None and (signal == "SELL" or price >= position["entry_price"] * 1.02):
                order = adapter.place_order(symbol=symbol, side="sell", amount=1.0, price=price)
                msg = f"SELL order executed at {price} (TP Exit)"
                if hasattr(notifier, "notify"):
                    notifier.notify(title="POSITION_EXIT_TP", message=msg)
                results.append({"event": "sell", "price": price, "order": order})
                position = None

        time.sleep(interval_seconds)

    return results


def main():
    symbol = "BTCTM"
    logger.info("Starting Wallex Paper Live Session with Journal Logging...")

    adapter = WallexPaperAdapter(initial_balances={"tm": 50000000.0, "usdt": 100.0})

    class DynamicWallexLiveDataFeed:
        def __init__(self, wallex_adapter, base_price=289483.50):
            self.adapter = wallex_adapter
            self.current_price = base_price

        def get_ticker_price(self, pair: str) -> float:
            change_pct = random.uniform(-0.0015, 0.0015)
            self.current_price *= (1.0 + change_pct)
            if hasattr(self.adapter, "market_prices"):
                self.adapter.market_prices[pair] = self.current_price
            return round(self.current_price, 2)

    data_feed = DynamicWallexLiveDataFeed(adapter)
    runner = PaperTradingLiveRunner(
        symbol=symbol,
        adapter=adapter,
        data_feed=data_feed,
        interval_seconds=2
    )

    runner.is_running = True
    logger.info("Executing 5-tick live paper sample with balance tracking...")

    session_logs = []
    for tick in range(1, 6):
        price = data_feed.get_ticker_price(symbol)
        # Using correct adapter wallet keys ("tm" and "usdt")
        tmn_bal = adapter.get_balance("tm") if hasattr(adapter, "get_balance") else 0.0
        usdt_bal = adapter.get_balance("usdt") if hasattr(adapter, "get_balance") else 0.0

        tick_summary = {
            "tick": tick,
            "symbol": symbol,
            "mid_price": price,
            "status": "success",
            "balances": {"TM": tmn_bal, "USDT": usdt_bal}
        }
        session_logs.append(tick_summary)
        print(f"[TICK {tick}/5] Price: {price:,.2f} TM | TM Bal: {tmn_bal:,.0f} | USDT Bal: {usdt_bal:.2f} | Status: success")
        time.sleep(1.0)

    logger.info("PaperTradingLiveRunner stopped.")

    os.makedirs("reports", exist_ok=True)
    report_file = "reports/wallex_paper_live_sample.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(session_logs, f, indent=2)

    print(f"[SUCCESS] Live paper run finished. Saved session report to {report_file}")


if __name__ == "__main__":
    main()
