import os
import sys
import json
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.adapters.wallex_paper import WallexPaperAdapter
import src.strategies.sma_cross as sma_mod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AtriaTrade.StrategyPaper")

STRATEGY_CLS = sma_mod.SMACrossStrategy


def main():
    symbol = "BTCTM"
    logger.info("Initializing Wallex Paper Strategy Execution...")
    logger.info(f"Strategy class: {STRATEGY_CLS.__module__}.{STRATEGY_CLS.__name__}")

    adapter = WallexPaperAdapter(initial_balances={"tm": 50_000_000.0, "usdt": 100.0})
    strategy = STRATEGY_CLS(short_window=2, long_window=4)

    prices = [
        289000.0, 290000.0, 291000.0, 292000.0,
        291000.0, 289500.0, 288000.0, 287000.0,
    ]

    trades = []
    position = None

    for i, price in enumerate(prices, 1):
        adapter.set_market_price(symbol, float(price))
        strategy.add_price(float(price))
        signal = strategy.generate_signal(float(price))

        logger.info(
            f"[Tick {i}/{len(prices)}] Price: {price:,.0f} TM | "
            f"Signal: {signal} | Position: {position}"
        )

        if signal == "BUY" and position is None:
            res = adapter.place_order(
                symbol=symbol, side="buy", order_type="market", amount=0.01
            )
            if res.get("status") == "success":
                position = {"entry": float(price), "amount": 0.01}
                trades.append({"action": "BUY", "price": price, "result": res["result"]})
                logger.info(f">>> BUY filled at {price:,.0f} TM")
            else:
                logger.warning(f">>> BUY rejected: {res}")

        elif signal == "SELL" and position is not None:
            res = adapter.place_order(
                symbol=symbol, side="sell", order_type="market", amount=position["amount"]
            )
            if res.get("status") == "success":
                pnl = (float(price) - position["entry"]) * position["amount"]
                trades.append(
                    {"action": "SELL", "price": price, "pnl": pnl, "result": res["result"]}
                )
                logger.info(f">>> SELL filled at {price:,.0f} TM | PnL: {pnl:+,.2f} TM")
                position = None
            else:
                logger.warning(f">>> SELL rejected: {res}")

    final_tm = adapter.get_balance("tm")
    final_usdt = adapter.get_balance("usdt")
    realized = sum(t.get("pnl", 0.0) for t in trades)
    logger.info(f"Final Balances -> TM: {final_tm:,.0f} | USDT: {final_usdt:.2f}")
    logger.info(f"Realized PnL (gross): {realized:+,.2f} TM | Trades: {len(trades)}")

    os.makedirs("reports", exist_ok=True)
    report_path = "reports/strategy_paper_run.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "strategy": f"{STRATEGY_CLS.__module__}.{STRATEGY_CLS.__name__}",
                "trades": trades,
                "final_balances": {"tm": final_tm, "usdt": final_usdt},
                "realized_pnl_gross": realized,
            },
            f,
            indent=2,
        )

    print(f"[SUCCESS] Strategy paper run completed. Report saved to {report_path}")


if __name__ == "__main__":
    main()
