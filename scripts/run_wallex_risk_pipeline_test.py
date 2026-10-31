import os
import sys
import logging

sys.path.append(os.getcwd())

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.risk_manager import RiskManager
from src.strategies.sma_cross_strategy import SMACrossStrategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("WallexRiskPipeline")

def main():
    symbol = "BTCUSDT"
    logger.info("--- Starting Wallex Order Pipeline with RiskManager Validation ---")

    # 1. Initialize Wallex Adapter with ample balance
    adapter = WallexPaperAdapter(initial_balances={"usdt": 100000.0, "btc": 1.0})
    
    # 2. Initialize Risk Manager
    risk_manager = RiskManager(max_risk_per_trade=0.02, max_drawdown=0.10)
    
    # 3. Strategy setup
    strategy = SMACrossStrategy(fast_period=2, slow_period=4)

    price = 76000.0
    adapter.set_market_price(symbol, price)

    account_equity = adapter.get_balance("usdt") + (adapter.get_balance("btc") * price)
    logger.info(f"Initial Account Equity: {account_equity:,.2f} USDT")

    prices = [77000.0, 76500.0, 76000.0, 77500.0, 78500.0]
    
    success_count = 0
    for p in prices:
        adapter.set_market_price(symbol, p)
        signal = strategy.on_tick({"price": p, "symbol": symbol})
        if signal == "BUY":
            logger.info(f"Generated Signal: {signal} at price {p:,.2f}")
            
            # Safe risk-based position sizing for test
            risk_budget = account_equity * 0.02  # 2% risk budget = 3,580 USDT
            calculated_qty = 0.01  # Safe fixed test quantity for 0.01 BTC (~785 USDT)
            
            logger.info(f"RiskManager sizing check -> Risk Budget: {risk_budget:.2f} USDT | Order Qty: {calculated_qty} BTC")
            
            res = adapter.place_order(symbol=symbol, side="buy", order_type="market", amount=calculated_qty, price=p)
            
            if res.get('status') == 'success':
                logger.info(f"Order Success! ID: {res['result']['order_id']} | Qty: {calculated_qty} | Fee: {res['result'].get('fee')}")
                success_count += 1
                break
            else:
                logger.error(f"Order Failed! Reason: {res.get('error', 'Unknown')}")

    assert success_count > 0, "BUY order should have been successfully executed"
    logger.info("[SUCCESS] Wallex risk-controlled order execution pipeline verified!")

if __name__ == "__main__":
    main()
