"""
Unit tests for TradeValidator.
"""

from src.core.trade_validator import TradeValidator


def test_validator():
    validator = TradeValidator(
        max_daily_loss_percent=5.0,
        max_capital_allocation_percent=25.0,
        minimum_risk_reward_ratio=1.5
    )

    # 1. Valid BUY signal
    res1 = validator.validate(
        side="BUY",
        entry_price=100.0,
        stop_loss_price=90.0,
        take_profit_price=120.0,
        capital=1000.0,
        allocated_capital=200.0,
        current_daily_loss_percent=1.0
    )
    assert res1["valid"] is True, f"Expected valid, got error: {res1.get('reason')}"
    assert res1["risk_reward_ratio"] == 2.0
    print("[OK] Valid BUY trade validation passed")

    # 2. Invalid side
    res2 = validator.validate(
        side="HOLD",
        entry_price=100.0,
        stop_loss_price=90.0,
        take_profit_price=120.0,
        capital=1000.0,
        allocated_capital=200.0
    )
    assert res2["valid"] is False
    assert "side must be BUY or SELL" in res2["errors"]
    print("[OK] Invalid side detection passed")

    # 3. Invalid Risk-Reward Ratio (below 1.5)
    res3 = validator.validate(
        side="BUY",
        entry_price=100.0,
        stop_loss_price=90.0,
        take_profit_price=110.0, # reward = 10, risk = 10 -> ratio = 1.0 < 1.5
        capital=1000.0,
        allocated_capital=200.0
    )
    assert res3["valid"] is False
    assert "risk reward ratio is below the minimum" in res3["errors"]
    print("[OK] Low Risk-Reward ratio rejection passed")

    # 4. Capital allocation exceeded (200/1000 = 20% is OK, 300/1000 = 30% exceeds 25%)
    res4 = validator.validate(
        side="BUY",
        entry_price=100.0,
        stop_loss_price=90.0,
        take_profit_price=120.0,
        capital=1000.0,
        allocated_capital=300.0
    )
    assert res4["valid"] is False
    assert "capital allocation exceeds configured maximum" in res4["errors"]
    print("[OK] High capital allocation rejection passed")

    # 5. Daily loss threshold exceeded
    res5 = validator.validate(
        side="BUY",
        entry_price=100.0,
        stop_loss_price=90.0,
        take_profit_price=120.0,
        capital=1000.0,
        allocated_capital=100.0,
        current_daily_loss_percent=5.1
    )
    assert res5["valid"] is False
    assert "maximum daily loss limit reached" in res5["errors"]
    print("[OK] Daily loss limit rejection passed")

    # 6. Invalid SL/TP positions for SELL
    res6 = validator.validate(
        side="SELL",
        entry_price=100.0,
        stop_loss_price=90.0, # For SELL, SL must be above entry
        take_profit_price=110.0, # For SELL, TP must be below entry
        capital=1000.0,
        allocated_capital=100.0
    )
    assert res6["valid"] is False
    assert "SELL stop loss must be above entry price" in res6["errors"]
    assert "SELL take profit must be below entry price" in res6["errors"]
    print("[OK] Invalid SELL SL/TP bounds rejection passed")

    print("=== TRADE VALIDATOR TEST PASSED ===")


if __name__ == "__main__":
    test_validator()
