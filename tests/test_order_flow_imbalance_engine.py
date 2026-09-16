"""Unit tests for OrderFlowImbalanceEngine (Capability 101)."""

import pytest
from src.core.order_flow_imbalance_engine import OrderFlowImbalanceEngine


@pytest.fixture
def engine():
    return OrderFlowImbalanceEngine(imbalance_threshold=1.5)


def test_estimate_candle_delta_bullish(engine):
    candle = {"open": 100.0, "high": 110.0, "low": 100.0, "close": 110.0, "volume": 1000.0}
    res = engine.estimate_candle_delta(candle)
    assert res["buy_vol"] == 1000.0
    assert res["sell_vol"] == 0.0
    assert res["delta"] == 1000.0
    assert res["imbalance_ratio"] == 999.0


def test_estimate_candle_delta_zero_volume(engine):
    candle = {"open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0, "volume": 0.0}
    res = engine.estimate_candle_delta(candle)
    assert res["delta"] == 0.0
    assert res["imbalance_ratio"] == 1.0


def test_analyze_order_flow_insufficient_data(engine):
    res = engine.analyze_order_flow([])
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["current_delta"] == 0.0


def test_analyze_order_flow_buying_imbalance(engine):
    candles = [
        {"open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 100.0},
        {"open": 101.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 500.0},
    ]
    res = engine.analyze_order_flow(candles)
    assert res["status"] == "VALID"
    assert res["imbalance_state"] == "BUYING_IMBALANCE"
    assert res["current_delta"] > 0


def test_analyze_order_flow_divergence_bearish(engine):
    # Price rises (100 -> 103 -> 106), but CVD drops due to massive selling absorption
    candles = [
        {"open": 100.0, "high": 102.0, "low": 99.0, "close": 100.0, "volume": 100.0}, # Close at mid/low -> small/flat delta
        {"open": 100.0, "high": 104.0, "low": 99.0, "close": 103.0, "volume": 200.0}, # Moderate delta
        {"open": 103.0, "high": 107.0, "low": 100.0, "close": 106.0, "volume": 5000.0}, # Close near top but let's test price higher with heavy selling
    ]
    # Candle 1: close 100, low 99, high 102 -> buy_weight=1/3, sell=2/3 -> delta = -33.33 (cvd = -33.33)
    # Candle 3: close 106 (higher than 100), range 100-110, close 101 -> buy_weight small, heavy sell delta -> cvd lower
    candles_div = [
        {"open": 100.0, "high": 102.0, "low": 100.0, "close": 102.0, "volume": 1000.0}, # delta = +1000, cvd = +1000
        {"open": 102.0, "high": 104.0, "low": 101.0, "close": 103.0, "volume": 500.0},
        {"open": 103.0, "high": 108.0, "low": 104.0, "close": 105.0, "volume": 4000.0}, # close=105 (>102), range 104-108, close 105 (weight 0.25) -> delta = -2000 -> cvd drops < +1000
    ]
    res = engine.analyze_order_flow(candles_div)
    assert res["status"] == "VALID"
    assert res["is_divergence"] is True
