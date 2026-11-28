import time
import sys
from src.adapters.paper_factory import PaperExchangeFactory
from src.strategies.sma_cross_strategy import SMACrossStrategy

def run_wallex_paper_live(symbol="USDTTMN", iterations=5, sleep_sec=3):
    print("=" * 55)
    print("  AtriaTrade - Wallex Paper Forward Testing Runner")
    print(f"  Target Symbol: {symbol} | Mode: 100% Simulated Execution")
    print("=" * 55)

    adapter = PaperExchangeFactory.create_adapter("wallex")
    strategy = SMACrossStrategy(fast_period=3, slow_period=5)

    initial_usdt = adapter.get_balance("USDT")
    initial_tmn = adapter.get_balance("TMN")
    print(f"[INIT] USDT Balance: {initial_usdt:.2f} | TMN Balance: {initial_tmn:,.0f}")

    for i in range(1, iterations + 1):
        print(f"\n--- Iteration {i}/{iterations} ---")
        try:
            ob = adapter.get_orderbook(symbol)
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])

            if not bids or not asks:
                print("[WARN] Incomplete orderbook received.")
                time.sleep(sleep_sec)
                continue

            best_bid = float(bids[0]["price"])
            best_ask = float(asks[0]["price"])
            mid_price = (best_bid + best_ask) / 2.0
            print(f"[MARKET] Bid: {best_bid:,.0f} | Ask: {best_ask:,.0f} | Mid: {mid_price:,.0f}")

            tick = {"price": mid_price, "volume": 1.0}
            signal = strategy.on_tick(tick)

            if signal:
                action = signal.get("action") if isinstance(signal, dict) else signal
                action_str = str(action).lower()
                print(f"[SIGNAL DETECTED] Action: {action_str.upper()}")

                if action_str in ["buy", "sell"]:
                    trade_res = adapter.place_order(
                        symbol=symbol,
                        side=action_str,
                        order_type="market",
                        amount=1.0
                    )
                    print(f"[EXECUTION] Status: {trade_res.get('status')} | Filled: {trade_res.get('result', {}).get('status')}")
            else:
                print("[STATUS] No trading signal generated.")

            cur_usdt = adapter.get_balance("USDT")
            cur_tmn = adapter.get_balance("TMN")
            print(f"[BALANCES] USDT: {cur_usdt:.2f} | TMN: {cur_tmn:,.0f}")

        except Exception as e:
            print(f"[ERROR] Cycle execution failure: {e}")

        if i < iterations:
            time.sleep(sleep_sec)

    print("\n" + "=" * 55)
    print("  Paper Forward Testing Session Completed Successfully")
    print("=" * 55)

if __name__ == "__main__":
    run_wallex_paper_live()
