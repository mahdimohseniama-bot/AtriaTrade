import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_runner_with_nobitex_adapter():
    # Initialize runner with Nobitex adapter and 100 USDT capital
    runner = PaperTradingLiveRunner(
        symbol="BTC/USDT",
        exchange_name="nobitex",
        initial_capital=100.0,
        risk_per_trade=0.02
    )

    assert runner.exchange.name == "nobitex"
    assert runner.capital_manager.current_capital == 100.0
    assert runner.capital_manager.vault_balance == 0.0

    # 1. Open Position: 0.0003 BTC @ 65,000 ~ 19.5 USDT (< 30% exposure limit)
    pos = runner.open_position(symbol="BTC/USDT", side="BUY", amount=0.0003)
    assert pos is not None
    assert pos["symbol"] == "BTC/USDT"
    assert pos["entry_price"] == 65000.0

    # 2. Close Position with Profit (+20 USDT Profit scenario: exit @ 131,666.66)
    # PnL = (131666.66 - 65000) * 0.0003 ~ 20.0
    closed = runner.close_position(symbol="BTC/USDT", exit_price=131666.6666667)
    assert closed is not None
    assert round(closed["pnl"], 1) == 20.0

    # 3. Verify 60/40 Split:
    # Profit = 20.0 -> 60% (12.0) to Vault, 40% (8.0) to Capital
    summary = runner.get_summary()
    assert summary["vault_balance"] == pytest.approx(12.0, rel=1e-2)
    assert summary["current_capital"] == pytest.approx(108.0, rel=1e-2)
    assert summary["total_wealth"] == pytest.approx(120.0, rel=1e-2)
    assert summary["completed_trades_count"] == 1

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_runner_exchange_integration.py"])
