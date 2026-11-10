import time
import logging
import argparse
from typing import Optional

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.risk_manager import RiskManager
from src.core.dynamic_position_protector import DynamicPositionProtector
from src.core.alert_notifier import AlertNotifier
from src.strategies.sma_cross_strategy import SMACrossStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("wallex_paper_live")

def run_loop(duration_seconds: int = 60, interval_seconds: int = 5, symbol: str = "BTCUSDT"):
    logger.info(f"Starting Wallex Paper Live Session for symbol: {symbol}")
    
    adapter = WallexPaperAdapter(initial_balances={"USDT": 1000.0, "BTC": 0.0})
    risk_manager = RiskManager(account_balance=1000.0, max_daily_loss=0.03, max_risk_per_trade=0.01)
    protector = DynamicPositionProtector(tp_pct=0.03, sl_pct=0.015)
    strategy = SMACrossStrategy(short_window=5, long_window=20)
    notifier = AlertNotifier()

    end_time = time.time() + duration_seconds
    cycle_count = 0

    while time.time() < end_time:
        cycle_count += 1
        logger.info(f"--- Cycle {cycle_count} ---")
        
        try:
            ticker = adapter.get_ticker(symbol)
            current_price = float(ticker.get("price", 0.0))
            if current_price <= 0:
                logger.warning(f"Invalid market price received: {current_price}")
                time.sleep(interval_seconds)
                continue

            logger.info(f"Market Price: {current_price}")

            # 1. Manage active position protection
            if protector.has_active_position():
                decision = protector.evaluate(current_price)
                if decision in ["TP", "SL"]:
                    logger.info(f"Protection triggered: {decision}. Exiting position at {current_price}...")
                    exit_order = adapter.place_order(
                        symbol=symbol,
                        side="sell",
                        order_type="market",
                        quantity=protector.position_size
                    )
                    logger.info(f"Exit order filled: {exit_order}")
                    notifier.notify(
                        title=f"POSITION_EXIT_{decision}",
                        message=f"Position closed via {decision} at price {current_price}",
                        level="INFO",
                        meta={"symbol": symbol, "exit_price": current_price, "reason": decision}
                    )
                    protector.close_position()
                    time.sleep(interval_seconds)
                    continue

            # 2. Risk check
            can_trade = risk_manager.can_trade_today()
            logger.info(f"Risk Check - Can Trade Today: {can_trade}")
            if not can_trade:
                logger.warning("Risk limits reached. Skipping signal evaluation.")
                notifier.notify(
                    title="RISK_LIMIT_HIT",
                    message="Trading halted for the day due to risk management parameters",
                    level="WARNING",
                    meta={"symbol": symbol}
                )
                time.sleep(interval_seconds)
                continue

            # 3. Strategy evaluation
            signal = strategy.generate_signal(current_price)
            logger.info(f"Strategy Signal: {signal}")

            # 4. Order execution
            if signal == "BUY" and not protector.has_active_position():
                qty = 0.001
                logger.info(f"Executing BUY order: {qty} {symbol} at {current_price}")
                order = adapter.place_order(
                    symbol=symbol,
                    side="buy",
                    order_type="market",
                    quantity=qty
                )
                logger.info(f"Order executed: {order}")
                protector.open_position(entry_price=current_price, size=qty)
                notifier.notify(
                    title="ORDER_BUY_FILLED",
                    message=f"Entered BUY position for {qty} {symbol} at {current_price}",
                    level="INFO",
                    meta={"symbol": symbol, "entry_price": current_price, "quantity": qty}
                )

        except Exception as e:
            logger.error(f"Error encountered during cycle {cycle_count}: {e}", exc_info=True)
            notifier.notify(
                title="RUNNER_CYCLE_ERROR",
                message=str(e),
                level="ERROR",
                meta={"cycle": cycle_count}
            )

        time.sleep(interval_seconds)

    logger.info("Wallex Paper Live Session finished successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wallex Paper Live Runner")
    parser.add_argument("--duration", type=int, default=60, help="Total execution duration in seconds")
    parser.add_argument("--interval", type=int, default=5, help="Loop interval in seconds")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    args = parser.parse_args()

    run_loop(duration_seconds=args.duration, interval_seconds=args.interval, symbol=args.symbol)
