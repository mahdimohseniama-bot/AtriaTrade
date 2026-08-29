"""
Unit tests for SMC Session & Asia Range Liquidity Tracker (Capability 88)
"""
import pytest
from src.core.session_liquidity_tracker import SessionLiquidityTracker

def test_asia_high_sweep_detected():
    tracker = SessionLiquidityTracker(sweep_buffer_pct=0.001)
    asia_high, asia_low = 2000.0, 1950.0
    # Candle pierces 2000 up to 2010 but closes back at 1995 in London session
    candle = {"open": 1990.0, "high": 2010.0, "low": 1988.0, "close": 1995.0}

    event = tracker.track_asia_sweep(candle, asia_high, asia_low, current_session="LONDON")
    assert event.detected is True
    assert event.sweep_type == "ASIA_HIGH_SWEEP"
    assert event.swept_level == 2000.0
    assert event.entry_price == 1995.0
    assert event.target_opposite_level == 1950.0
    assert event.suggested_stop_loss == 2010.0

def test_asia_low_sweep_detected():
    tracker = SessionLiquidityTracker(sweep_buffer_pct=0.001)
    asia_high, asia_low = 100.0, 90.0
    # Candle drops to 88 then closes back at 92
    candle = {"open": 91.0, "high": 93.0, "low": 88.0, "close": 92.0}

    event = tracker.track_asia_sweep(candle, asia_high, asia_low, current_session="NY")
    assert event.detected is True
    assert event.sweep_type == "ASIA_LOW_SWEEP"
    assert event.swept_level == 90.0
    assert event.entry_price == 92.0
    assert event.target_opposite_level == 100.0
    assert event.suggested_stop_loss == 88.0

def test_breakout_without_rejection_is_not_sweep():
    tracker = SessionLiquidityTracker()
    asia_high, asia_low = 100.0, 90.0
    # Candle breaks above and closes outside at 105
    candle = {"open": 99.0, "high": 106.0, "low": 98.0, "close": 105.0}
    event = tracker.track_asia_sweep(candle, asia_high, asia_low)
    assert event.detected is False
    assert event.sweep_type == "NONE"

def test_inside_asia_range_no_sweep():
    tracker = SessionLiquidityTracker()
    asia_high, asia_low = 100.0, 90.0
    # Candle stays completely within the range
    candle = {"open": 95.0, "high": 97.0, "low": 93.0, "close": 96.0}
    event = tracker.track_asia_sweep(candle, asia_high, asia_low)
    assert event.detected is False
    assert event.sweep_type == "NONE"

def test_invalid_asia_range_bounds():
    tracker = SessionLiquidityTracker()
    candle = {"open": 95.0, "high": 97.0, "low": 93.0, "close": 96.0}
    # Invalid bounds (high <= low or negative)
    event = tracker.track_asia_sweep(candle, asia_high=90.0, asia_low=100.0)
    assert event.detected is False
    assert "Invalid Asia session bounds" in event.reason

def test_invalid_candle_data():
    tracker = SessionLiquidityTracker()
    # Invalid candle (high <= low)
    candle = {"open": 95.0, "high": 90.0, "low": 95.0, "close": 92.0}
    event = tracker.track_asia_sweep(candle, asia_high=100.0, asia_low=80.0)
    assert event.detected is False
    assert "Invalid candle data" in event.reason
