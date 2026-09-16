import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.capital_manager import CapitalManager
from src.core.risk_manager import RiskManager, RiskConfig
from src.core.trader_engine import TraderEngine

def run_test():
    print("\n[1] Initializing Engine with realistic capital & risk...")
    # سرمایه بیشتر تا از حداقل ارزش معامله عبور کنیم
    cap_mgr = CapitalManager(initial_capital=10000.0)
    
    # تنظیم ریسک کمی آزادتر برای تست
    risk_cfg = RiskConfig(
        risk_per_trade_pct=1.0,   # 1% از 10000 = 100 دلار ریسک هر معامله
        max_position_pct=10.0,
        max_daily_loss_pct=3.0,
        max_drawdown_pct=15.0,
        max_consecutive_losses=3,
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
        trailing_stop_pct=1.0,
        min_trade_value=10.0,     # حالا 100 دلار > 10 دلار، پس منطقیه
        fee_buffer_pct=0.2
    )
    
    risk_mgr = RiskManager(risk_cfg)
    engine = TraderEngine(capital_manager=cap_mgr, risk_manager=risk_mgr)
    
    status = engine.get_portfolio_summary()["capital_status"]
    print(f"Status: {status}")

    print("\n[2] Simulating Trade (BUY BTC @ 50000)")
    pos = engine.open_virtual_position(symbol="BTC/USDT", side="buy", current_price=50000.0)
    
    if pos is None:
        raise AssertionError("Trade was rejected: Risk or position size invalid.")
    
    print(f"-> SUCCESS: Opened {pos.side.upper()} {pos.symbol}")
    print(f"-> Size: {pos.size:.6f}, SL: {pos.stop_loss}, TP: {pos.take_profit}")

    print("\n[3] Simulating Exit (SELL BTC @ 51000 - PROFIT)")
    closed_pos = engine.close_virtual_position(symbol="BTC/USDT", exit_price=51000.0)
    
    if closed_pos is None:
        raise AssertionError("Failed to close position.")
    
    print(f"-> SUCCESS: Trade Closed. PNL: {closed_pos.pnl:.2f}")

    print(f"\n[4] Final Portfolio Status:")
    summary = engine.get_portfolio_summary()
    for k, v in summary['capital_status'].items():
        print(f"   {k}: {v}")
    
    print("\n=== INTEGRATION TEST PASSED (OPEN & CLOSE VIRTUAL POSITION) ===")

if __name__ == "__main__":
    run_test()
