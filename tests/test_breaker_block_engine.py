"""
Unit tests for SMC Breaker Block & Mitigation Engine (Capability 87)
"""
import pytest
from src.core.breaker_block_engine import BreakerBlockEngine

def test_bullish_breaker_block_reaction():
    engine = BreakerBlockEngine(tolerance_pct=0.001)
    broken_ob = {"original_type": "BEARISH_OB", "high": 105.0, "low": 100.0}
    # Retest into 100-105 zone from above
    candle = {"open": 107.0, "high": 107.5, "low": 102.0, "close": 104.0}

    signal = engine.detect_breaker(candle, broken_ob, market_structure="BULLISH")
    assert signal.detected is True
    assert signal.block_type == "BULLISH_BREAKER"
    assert signal.zone_high == 105.0
    assert signal.zone_low == 100.0
    assert signal.entry_price == 104.0
    assert signal.suggested_stop_loss < 100.0

def test_bearish_breaker_block_reaction():
    engine = BreakerBlockEngine(tolerance_pct=0.001)
    broken_ob = {"original_type": "BULLISH_OB", "high": 200.0, "low": 195.0}
    # Retest into 195-200 zone from below
    candle = {"open": 190.0, "high": 198.0, "low": 189.0, "close": 196.0}

    signal = engine.detect_breaker(candle, broken_ob, market_structure="BEARISH")
    assert signal.detected is True
    assert signal.block_type == "BEARISH_BREAKER"
    assert signal.entry_price == 196.0
    assert signal.suggested_stop_loss > 200.0

def test_no_reaction_when_price_outside_zone():
    engine = BreakerBlockEngine()
    broken_ob = {"original_type": "BEARISH_OB", "high": 105.0, "low": 100.0}
    candle = {"open": 120.0, "high": 122.0, "low": 118.0, "close": 119.0}

    signal = engine.detect_breaker(candle, broken_ob, market_structure="BULLISH")
    assert signal.detected is False

def test_structure_mismatch_ignored():
    engine = BreakerBlockEngine()
    broken_ob = {"original_type": "BEARISH_OB", "high": 105.0, "low": 100.0}
    # Bullish breaker requires Bullish market structure
    candle = {"open": 107.0, "high": 107.5, "low": 102.0, "close": 104.0}
    signal = engine.detect_breaker(candle, broken_ob, market_structure="BEARISH")
    assert signal.detected is False

def test_invalid_candle_data():
    engine = BreakerBlockEngine()
    broken_ob = {"original_type": "BEARISH_OB", "high": 105.0, "low": 100.0}
    candle = {"open": 100.0, "high": 90.0, "low": 100.0, "close": 95.0} # high <= low
    signal = engine.detect_breaker(candle, broken_ob)
    assert signal.detected is False
    assert "Invalid candle" in signal.reason

def test_empty_or_invalid_broken_ob():
    engine = BreakerBlockEngine()
    candle = {"open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0}
    signal = engine.detect_breaker(candle, {})
    assert signal.detected is False
