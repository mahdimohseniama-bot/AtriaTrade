"""
Unit tests for SMC Equilibrium & Premium/Discount Matrix (Capability 89)
"""
import pytest
from src.core.equilibrium_matrix import EquilibriumMatrix

def test_discount_zone_allows_long_only():
    matrix = EquilibriumMatrix()
    # High: 200, Low: 100 -> EQ = 150. Price: 120 (20% of range -> Deep Discount)
    res = matrix.evaluate_zone(current_price=120.0, range_high=200.0, range_low=100.0)
    assert res.zone == "DEEP_DISCOUNT"
    assert res.equilibrium == 150.0
    assert res.long_allowed is True
    assert res.short_allowed is False

def test_premium_zone_allows_short_only():
    matrix = EquilibriumMatrix()
    # High: 200, Low: 100 -> EQ = 150. Price: 170 (70% of range -> Premium)
    res = matrix.evaluate_zone(current_price=170.0, range_high=200.0, range_low=100.0)
    assert res.zone == "PREMIUM"
    assert res.long_allowed is False
    assert res.short_allowed is True

def test_equilibrium_neutral_buffer():
    matrix = EquilibriumMatrix(eq_buffer_pct=0.02)
    # Range 100 to 200, EQ is 150. Price 151 is within 2% buffer of 50%
    res = matrix.evaluate_zone(current_price=151.0, range_high=200.0, range_low=100.0)
    assert res.zone == "EQUILIBRIUM"
    assert res.long_allowed is True
    assert res.short_allowed is True

def test_signal_validation_rejects_buy_in_premium():
    matrix = EquilibriumMatrix()
    val = matrix.validate_signal_direction(
        signal_type="BUY",
        current_price=180.0,
        range_high=200.0,
        range_low=100.0
    )
    assert val["valid"] is False
    assert "Cannot buy in EXTREME_PREMIUM zone" in val["reason"]

def test_signal_validation_confirms_sell_in_premium():
    matrix = EquilibriumMatrix()
    val = matrix.validate_signal_direction(
        signal_type="SELL",
        current_price=180.0,
        range_high=200.0,
        range_low=100.0
    )
    assert val["valid"] is True
    assert val["evaluation"].zone == "EXTREME_PREMIUM"

def test_invalid_range_handling():
    matrix = EquilibriumMatrix()
    res = matrix.evaluate_zone(current_price=100.0, range_high=50.0, range_low=100.0)
    assert res.zone == "INVALID"
    assert res.long_allowed is False
    assert res.short_allowed is False
