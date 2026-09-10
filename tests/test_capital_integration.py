import pytest
from src.core.capital_manager import CapitalManager
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.portfolio_risk import PortfolioRiskManager

def test_compound_and_reserve_cycle():
    print("\n=======================================================")
    print("  [TEST] Capital Manager 60/40 Compound Cycle")
    print("=======================================================")

    # max_single_asset_exposure_pct is by default 0.30 (30%)
    risk = PortfolioRiskManager(
        max_total_exposure_pct=0.80, 
        max_single_asset_exposure_pct=0.30,
        max_open_positions=2
    )
    capital = CapitalManager(initial_capital=100.0, vault_ratio=0.60, compound_ratio=0.40)
    
    runner = PaperTradingLiveRunner(
        symbol="BTC/USDT", 
        initial_balance=100.0,
        risk_manager=risk, 
        capital_manager=capital
    )

    # 1. Open a valid position:
    # Size = 0.0004 @ 50,000 USDT -> Value = 20 USDT (20% of 100 <= 30% max limit)
    opened = runner.open_position("BTC/USDT", size=0.0004, price=50000.0, side="BUY")
    assert opened is True
    assert "BTC/USDT" in runner.positions

    # 2. Close with profit (exit at 75,000 USDT):
    # Raw PnL = (75,000 - 50,000) * 0.0004 = 25,000 * 0.0004 = +10.0 USDT
    # 60% Vault = 6.0 USDT
    # 40% Active Compound = 4.0 USDT -> Active Capital = 104.0 USDT
    trade = runner.close_position("BTC/USDT", exit_price=75000.0)
    assert trade is not None
    assert trade["pnl"] == 10.0
    
    status = runner.capital_manager.get_status()
    assert status["profit_reserve"] == 6.0
    assert status["current_capital"] == 104.0
    assert status["total_value"] == 110.0
    print(f"\n[PASS] Cycle completed successfully with Status: {status}")

def test_recovery_on_loss_before_compound():
    capital = CapitalManager(initial_capital=100.0, vault_ratio=0.60, compound_ratio=0.40)
    
    # First trade: Loss of 10 USDT
    capital.record_trade_result(-10.0)
    assert capital.current_capital == 90.0
    assert capital.profit_reserve == 0.0

    # Second trade: Win 15 USDT
    # First 10 USDT recovers capital back to 100.0
    # Remaining 5 USDT splits 60% Vault (3.0) and 40% Compound (2.0)
    capital.record_trade_result(15.0)
    assert capital.current_capital == 102.0
    assert capital.profit_reserve == 3.0
    assert capital.get_status()["total_value"] == 105.0

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_capital_integration.py"])
