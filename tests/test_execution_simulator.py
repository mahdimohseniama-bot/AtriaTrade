"""
Tests for ExecutionSimulator - AtriaTrade
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.execution_simulator import ExecutionSimulator


def test_initialization():
    simulator = ExecutionSimulator(initial_cash=10000, fee_pct=0.1)

    status = simulator.get_status()

    assert status["cash"] == 10000.0
    assert status["equity"] == 10000.0
    assert status["trade_count"] == 0
    assert status["real_trading_enabled"] is False

    print("PASS: test_initialization")


def test_buy_order():
    simulator = ExecutionSimulator(initial_cash=10000, fee_pct=0.1)

    result = simulator.execute(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.1,
        price=1000,
    )

    assert result["status"] == "filled"
    assert result["side"] == "BUY"
    assert result["fee"] == 0.1
    assert result["position_after"] == 0.1
    assert result["order_submitted"] is False

    print("PASS: test_buy_order")


def test_sell_order_and_pnl():
    simulator = ExecutionSimulator(initial_cash=10000, fee_pct=0.1)

    simulator.execute("BTCUSDT", "BUY", 1, 1000)
    result = simulator.execute("BTCUSDT", "SELL", 1, 1200)

    assert result["status"] == "filled"
    assert result["position_after"] == 0.0
    assert result["realized_pnl"] > 0
    assert simulator.realized_pnl > 0

    print("PASS: test_sell_order_and_pnl")


def test_insufficient_cash():
    simulator = ExecutionSimulator(initial_cash=100)

    result = simulator.execute("BTCUSDT", "BUY", 1, 1000)

    assert result["status"] == "rejected"
    assert result["reason"] == "insufficient_cash"
    assert simulator.trade_count == 0

    print("PASS: test_insufficient_cash")


def test_insufficient_position():
    simulator = ExecutionSimulator(initial_cash=10000)

    result = simulator.execute("BTCUSDT", "SELL", 1, 1000)

    assert result["status"] == "rejected"
    assert result["reason"] == "insufficient_position"
    assert simulator.trade_count == 0

    print("PASS: test_insufficient_position")


def test_mark_to_market():
    simulator = ExecutionSimulator(initial_cash=10000, fee_pct=0)

    simulator.execute("ETHUSDT", "BUY", 2, 1000)

    equity = simulator.mark_to_market({"ETHUSDT": 1200})

    assert equity == 10400.0

    print("PASS: test_mark_to_market")


def test_invalid_values():
    invalid_cases = [
        ("BTCUSDT", "BUY", 0, 1000),
        ("BTCUSDT", "BUY", 1, 0),
        ("BTCUSDT", "INVALID", 1, 1000),
    ]

    simulator = ExecutionSimulator()

    for args in invalid_cases:
        try:
            simulator.execute(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {args}")

    print("PASS: test_invalid_values")


if __name__ == "__main__":
    print("START: ExecutionSimulator Tests")

    test_initialization()
    test_buy_order()
    test_sell_order_and_pnl()
    test_insufficient_cash()
    test_insufficient_position()
    test_mark_to_market()
    test_invalid_values()

    print("ALL ExecutionSimulator TESTS PASSED SUCCESSFULLY!")
