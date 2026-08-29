import pytest
from src.core.ote_engine import (
    OTEEngine,
    TrendDirection,
    OTEZone
)


def test_bullish_retracement_levels():
    engine = OTEEngine()
    swing_low = 100.0
    swing_high = 200.0
    levels = engine.calculate_retracement_levels(swing_low, swing_high, TrendDirection.BULLISH)

    assert levels["0.0"] == 200.0
    assert levels["0.500"] == 150.0
    assert levels["0.618"] == 138.2
    assert levels["0.705"] == 129.5
    assert levels["0.786"] == 121.4
    assert levels["1.0"] == 100.0


def test_bearish_retracement_levels():
    engine = OTEEngine()
    swing_low = 100.0
    swing_high = 200.0
    levels = engine.calculate_retracement_levels(swing_low, swing_high, TrendDirection.BEARISH)

    assert levels["0.0"] == 100.0
    assert levels["0.500"] == 150.0
    assert levels["0.618"] == 161.8
    assert levels["0.705"] == 170.5
    assert levels["0.786"] == 178.6
    assert levels["1.0"] == 200.0


def test_ote_zone_generation_and_validation():
    engine = OTEEngine()
    zone = engine.generate_ote_zone(swing_low=100.0, swing_high=200.0, direction=TrendDirection.BULLISH)

    assert zone.direction == TrendDirection.BULLISH
    assert zone.optimal_entry == 129.5
    assert zone.stop_loss_level < 100.0
    assert zone.take_profit_level == 200.0

    # In zone check
    assert engine.is_price_in_ote_zone(130.0, zone) is True
    assert engine.is_price_in_ote_zone(138.2, zone) is True
    assert engine.is_price_in_ote_zone(121.4, zone) is True
    assert engine.is_price_in_ote_zone(160.0, zone) is False
    assert engine.is_price_in_ote_zone(95.0, zone) is False


def test_invalid_parameters():
    engine = OTEEngine()
    with pytest.raises(ValueError):
        engine.calculate_retracement_levels(swing_low=200.0, swing_high=100.0, direction=TrendDirection.BULLISH)

    with pytest.raises(ValueError):
        OTEEngine(sweet_spot_fib=1.5)
