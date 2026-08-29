"""
Unit tests for Optimal Trade Entry (OTE) Engine (Capability 94)
"""

import pytest
from src.core.ote_engine import OTEEngine, TradeDirection, MarketZone


def test_ote_calculation_bullish_long():
    engine = OTEEngine()
    # Swing Low = 100, Swing High = 200 (diff = 100)
    profile = engine.calculate_ote(swing_low=100.0, swing_high=200.0, direction=TradeDirection.LONG)

    assert profile.equilibrium == 150.0
    assert profile.ote_618 == 138.2   # 200 - 61.8
    assert profile.ote_705 == 129.5   # 200 - 70.5
    assert profile.ote_786 == 121.4   # 200 - 78.6
    assert profile.target_ext_27 == 227.0
    assert profile.target_ext_62 == 262.0


def test_ote_calculation_bearish_short():
    engine = OTEEngine()
    # Swing Low = 100, Swing High = 200 (diff = 100)
    profile = engine.calculate_ote(swing_low=100.0, swing_high=200.0, direction=TradeDirection.SHORT)

    assert profile.equilibrium == 150.0
    assert profile.ote_618 == 161.8   # 100 + 61.8
    assert profile.ote_705 == 170.5   # 100 + 70.5
    assert profile.ote_786 == 178.6   # 100 + 78.6
    assert profile.target_ext_27 == 73.0
    assert profile.target_ext_62 == 38.0


def test_market_zone_classification():
    engine = OTEEngine()
    # Swing: 100 to 200, EQ = 150
    assert engine.get_market_zone(price=175.0, swing_low=100.0, swing_high=200.0) == MarketZone.PREMIUM
    assert engine.get_market_zone(price=125.0, swing_low=100.0, swing_high=200.0) == MarketZone.DISCOUNT
    assert engine.get_market_zone(price=150.0, swing_low=100.0, swing_high=200.0) == MarketZone.EQUILIBRIUM


def test_is_in_ote_zone_validation():
    engine = OTEEngine()
    # Long OTE: [121.4, 138.2]
    profile_long = engine.calculate_ote(swing_low=100.0, swing_high=200.0, direction=TradeDirection.LONG)
    assert engine.is_in_ote_zone(130.0, profile_long) is True
    assert engine.is_in_ote_zone(121.4, profile_long) is True
    assert engine.is_in_ote_zone(138.2, profile_long) is True
    assert engine.is_in_ote_zone(145.0, profile_long) is False
    assert engine.is_in_ote_zone(115.0, profile_long) is False

    # Short OTE: [161.8, 178.6]
    profile_short = engine.calculate_ote(swing_low=100.0, swing_high=200.0, direction=TradeDirection.SHORT)
    assert engine.is_in_ote_zone(170.0, profile_short) is True
    assert engine.is_in_ote_zone(155.0, profile_short) is False


def test_invalid_swing_extremes():
    engine = OTEEngine()
    with pytest.raises(ValueError, match="swing_high must be strictly greater than swing_low"):
        engine.calculate_ote(swing_low=200.0, swing_high=100.0, direction=TradeDirection.LONG)

    with pytest.raises(ValueError, match="swing_high must be strictly greater than swing_low"):
        engine.get_market_zone(price=150.0, swing_low=200.0, swing_high=200.0)
