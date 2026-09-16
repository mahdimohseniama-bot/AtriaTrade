"""
Tests for Advanced RiskManager.
"""

from src.core.risk_manager import RiskManager


def test_level_calculations():
    rm = RiskManager(default_risk_reward_ratio=2.0)

    # Test BUY levels with percentage
    levels_buy = rm.calculate_levels(
        entry_price=100.0,
        side="BUY",
        stop_loss_distance_percent=2.0,
    )
    assert levels_buy["stop_loss"] == 98.0
    assert levels_buy["take_profit"] == 104.0
    assert levels_buy["risk_distance"] == 2.0

    # Test SELL levels with explicit price
    levels_sell = rm.calculate_levels(
        entry_price=100.0,
        side="SELL",
        stop_loss_price=105.0,
    )
    assert levels_sell["stop_loss"] == 105.0
    assert levels_sell["take_profit"] == 90.0
    assert levels_sell["risk_distance"] == 5.0


def test_position_sizing_standard():
    rm = RiskManager(
        default_risk_per_trade_percent=1.0,
        max_capital_allocation_percent=50.0,
    )

    # Capital 10,000 | 1% risk = 100 USD
    # Entry 100, SL 98 -> Risk per unit = 2 USD
    # Units = 100 / 2 = 50 units | Allocated = 50 * 100 = 5000 USD (50% max allowed)
    sizing = rm.calculate_position_size(
        capital=10000.0,
        entry_price=100.0,
        stop_loss_price=98.0,
        side="BUY",
    )
    assert sizing["units"] == 50.0
    assert sizing["allocated_capital"] == 5000.0
    assert sizing["risk_amount"] == 100.0
    assert sizing["is_capped"] is False


def test_position_sizing_capped():
    rm = RiskManager(
        default_risk_per_trade_percent=2.0,
        max_capital_allocation_percent=20.0,
    )

    # Capital 10,000 | 2% risk = 200 USD | Max cap = 20% = 2000 USD
    # Entry 100, SL 99 -> Risk per unit = 1 USD -> Raw units = 200 -> Raw alloc = 20,000 USD (Exceeds 2000)
    # Capped units = 2000 / 100 = 20 units
    sizing = rm.calculate_position_size(
        capital=10000.0,
        entry_price=100.0,
        stop_loss_price=99.0,
        side="BUY",
    )
    assert sizing["units"] == 20.0
    assert sizing["allocated_capital"] == 2000.0
    assert sizing["is_capped"] is True
    assert sizing["risk_amount"] == 20.0


def test_daily_risk_validation():
    rm = RiskManager(max_daily_loss_percent=5.0)

    safe_status = rm.validate_daily_risk(current_daily_loss_percent=3.2)
    assert safe_status["trading_allowed"] is True

    halt_status = rm.validate_daily_risk(current_daily_loss_percent=5.0)
    assert halt_status["trading_allowed"] is False
    assert halt_status["reason"] == "Max daily loss limit reached"


def test_risk_manager():
    print("========================================")
    print("START: RiskManager Tests")
    print("========================================")

    test_level_calculations()
    print("[OK] Level calculations (SL/TP) passed")

    test_position_sizing_standard()
    print("[OK] Standard position sizing passed")

    test_position_sizing_capped()
    print("[OK] Capped position sizing passed")

    test_daily_risk_validation()
    print("[OK] Daily risk validation passed")

    print("========================================")
    print("=== RISK MANAGER TEST PASSED ===")
    print("========================================")


if __name__ == "__main__":
    test_risk_manager()
