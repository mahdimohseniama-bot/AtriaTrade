"""
Tests for IntegratedTradingPipeline - AtriaTrade
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.integrated_pipeline import IntegratedTradingPipeline


def test_pipeline_initialization():
    pipeline = IntegratedTradingPipeline(initial_cash=10000.0, mode="paper")
    status = pipeline.get_full_status()

    assert status["mode"] == "paper"
    assert status["equity"] == 10000.0
    assert status["real_trading_enabled"] is False
    assert status["order_submitted"] is False
    print("PASS: test_pipeline_initialization")


def test_integrated_buy_and_sell_flow():
    def dummy_strategy(data):
        return {"action": data.get("action", "HOLD"), "confidence": 0.95}

    pipeline = IntegratedTradingPipeline(
        initial_cash=10000.0,
        fee_pct=0.1,
        mode="paper",
        strategy_callback=dummy_strategy,
    )

    # 1. Execute BUY
    buy_res = pipeline.process_tick(
        symbol="BTCUSDT",
        price=50000.0,
        quantity=0.1,
        strategy_signal="BUY",
    )
    assert buy_res["action"] == "BUY"
    assert buy_res["execution"]["status"] == "filled"
    assert buy_res["order_submitted"] is False
    assert pipeline.simulator.positions.get("BTCUSDT", 0.0) == 0.1

    # 2. Execute SELL with profit
    sell_res = pipeline.process_tick(
        symbol="BTCUSDT",
        price=55000.0,
        quantity=0.1,
        strategy_signal="SELL",
    )
    assert sell_res["action"] == "SELL"
    assert sell_res["execution"]["status"] == "filled"
    assert sell_res["execution"]["realized_pnl"] > 0
    assert pipeline.simulator.positions.get("BTCUSDT", 0.0) == 0.0

    print("PASS: test_integrated_buy_and_sell_flow")


def test_emergency_circuit_breaker_blocks_trading():
    def dummy_strategy(data):
        return {"action": "BUY", "confidence": 0.9}

    pipeline = IntegratedTradingPipeline(
        initial_cash=10000.0,
        mode="paper",
        strategy_callback=dummy_strategy,
    )

    # Trigger emergency breaker
    pipeline.recovery_manager.activate_emergency_stop("Safety trigger test")

    res = pipeline.process_tick(
        symbol="ETHUSDT",
        price=2000.0,
        quantity=1.0,
        strategy_signal="BUY",
    )

    assert res["action"] == "HOLD"
    assert res["order_submitted"] is False
    assert pipeline.simulator.trade_count == 0

    print("PASS: test_emergency_circuit_breaker_blocks_trading")


def test_hold_decision_leaves_state_clean():
    pipeline = IntegratedTradingPipeline(initial_cash=5000.0, mode="paper")

    res = pipeline.process_tick(
        symbol="SOLUSDT",
        price=100.0,
        quantity=1.0,
        strategy_signal="HOLD",
    )

    assert res["action"] == "HOLD"
    assert pipeline.simulator.trade_count == 0
    assert pipeline.simulator.cash == 5000.0

    print("PASS: test_hold_decision_leaves_state_clean")


if __name__ == "__main__":
    print("START: IntegratedTradingPipeline Tests")

    test_pipeline_initialization()
    test_integrated_buy_and_sell_flow()
    test_emergency_circuit_breaker_blocks_trading()
    test_hold_decision_leaves_state_clean()

    print("ALL IntegratedTradingPipeline TESTS PASSED SUCCESSFULLY!")
