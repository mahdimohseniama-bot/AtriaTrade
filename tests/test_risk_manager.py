from __future__ import annotations

import math
from src.core.risk_manager import RiskManager


def test_risk_calculations() -> None:
    print("[1] Creating RiskManager...")
    manager = RiskManager(
        capital=10000.0,
        max_risk_percent=1.0,
        max_position_percent=50.0,
        max_daily_loss_percent=5.0,
    )

    print("[2] Calculating risk amount...")
    risk_amount = manager.calculate_risk_amount()
    assert math.isclose(risk_amount, 100.0)
    print("-> Risk amount calculated successfully.")

    print("[3] Calculating position size...")
    size = manager.calculate_position_size(
        entry_price=50000.0,
        stop_loss=49000.0,
    )
    assert math.isclose(size, 0.1)
    print("-> Position size calculated successfully.")

    print("[4] Testing daily loss and trading limits...")
    assert manager.can_trade_today() is True

    manager.record_daily_loss(400.0)
    assert manager.can_trade_today() is True

    manager.record_daily_loss(150.0)
    assert manager.can_trade_today() is False

    manager.reset_daily_loss()
    assert manager.can_trade_today() is True

    print("=== RISK MANAGER TEST PASSED ===")


def test_risk_validation_errors() -> None:
    manager = RiskManager(capital=10000.0)

    invalid_calls = [
        lambda: manager.calculate_position_size(entry_price=0, stop_loss=49000),
        lambda: manager.calculate_position_size(entry_price=50000, stop_loss=-100),
        lambda: manager.calculate_position_size(entry_price=50000, stop_loss=50000),
        lambda: manager.record_daily_loss(-50.0),
        lambda: RiskManager(capital=-1000),
    ]

    for invalid_call in invalid_calls:
        try:
            invalid_call()
            raise AssertionError("Invalid risk input was accepted.")
        except ValueError:
            pass

    print("=== RISK VALIDATION TEST PASSED ===")


if __name__ == "__main__":
    test_risk_calculations()
    test_risk_validation_errors()
