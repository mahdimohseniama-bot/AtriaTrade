"""Unit tests for LiquiditySweepEngine (Capability 103)."""

import pytest
from src.core.liquidity_sweep_engine import LiquiditySweepEngine


@pytest.fixture
def engine():
    return LiquiditySweepEngine(swing_lookback=2, sweep_tolerance_pct=0.002)


def test_insufficient_data(engine):
    res = engine.analyze_latest_sweep([])
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["sweep_type"] == "NONE"


def test_bearish_sweep_detection(engine):
    # Form a swing high at index 2 (price 105.0)
    candles = [
        {"open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0},
        {"open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0},
        {"open": 102.0, "high": 105.0, "low": 101.0, "close": 104.0}, # Swing High
        {"open": 104.0, "high": 103.0, "low": 100.0, "close": 101.0},
        {"open": 101.0, "high": 102.0, "low": 99.0, "close": 100.0},
        # Latest candle sweeps above 105.0 up to 106.0 but closes at 103.0
        {"open": 100.0, "high": 106.0, "low": 99.0, "close": 103.0},
    ]
    res = engine.analyze_latest_sweep(candles)
    assert res["status"] == "SWEEP_DETECTED"
    assert res["sweep_type"] == "BEARISH_SWEEP"
    assert res["swept_level"] == 105.0
    assert res["wick_excursion"] == 106.0


def test_bullish_sweep_detection(engine):
    # Form a swing low at index 2 (price 95.0)
    candles = [
        {"open": 100.0, "high": 101.0, "low": 98.0, "close": 99.0},
        {"open": 99.0, "high": 100.0, "low": 97.0, "close": 98.0},
        {"open": 98.0, "high": 99.0, "low": 95.0, "close": 96.0}, # Swing Low
        {"open": 96.0, "high": 98.0, "low": 96.0, "close": 97.0},
        {"open": 97.0, "high": 99.0, "low": 97.0, "close": 98.0},
        # Latest candle sweeps below 95.0 down to 94.0 but closes at 97.0
        {"open": 98.0, "high": 99.0, "low": 94.0, "close": 97.0},
    ]
    res = engine.analyze_latest_sweep(candles)
    assert res["status"] == "SWEEP_DETECTED"
    assert res["sweep_type"] == "BULLISH_SWEEP"
    assert res["swept_level"] == 95.0
    assert res["wick_excursion"] == 94.0
