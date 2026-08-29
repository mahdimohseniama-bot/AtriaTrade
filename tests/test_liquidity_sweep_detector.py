"""
Unit tests for SMC Liquidity Sweep & Stop Hunt Detector (Capability 86)
"""
import pytest
from src.core.liquidity_sweep_detector import LiquiditySweepDetector

def test_bullish_liquidity_sweep_detected():
    detector = LiquiditySweepDetector(min_wick_ratio=0.3, min_sweep_pct=0.001)
    # Key support low is 100.0; candle drops to 98.0 (2% sweep) then closes inside at 102.0
    candle = {"open": 101.0, "high": 103.0, "low": 98.0, "close": 102.0}

    event = detector.detect_sweep(candle, key_low=100.0)
    assert event.detected is True
    assert event.sweep_type == "BULLISH_SWEEP"
    assert event.swept_level == 100.0
    assert event.entry_price == 102.0
    assert event.suggested_stop_loss == 98.0
    assert event.wick_ratio > 0.3

def test_bearish_liquidity_sweep_detected():
    detector = LiquiditySweepDetector(min_wick_ratio=0.3, min_sweep_pct=0.001)
    # Key resistance high is 200.0; candle pumps to 205.0 then closes back at 198.0
    candle = {"open": 199.0, "high": 205.0, "low": 197.0, "close": 198.0}

    event = detector.detect_sweep(candle, key_high=200.0)
    assert event.detected is True
    assert event.sweep_type == "BEARISH_SWEEP"
    assert event.swept_level == 200.0
    assert event.entry_price == 198.0
    assert event.suggested_stop_loss == 205.0
    assert event.wick_ratio > 0.3

def test_clean_breakout_not_a_sweep():
    detector = LiquiditySweepDetector()
    # Clean breakout closes outside the level (no rejection wick)
    candle = {"open": 199.0, "high": 205.0, "low": 198.0, "close": 204.0}
    event = detector.detect_sweep(candle, key_high=200.0)
    assert event.detected is False

def test_insufficient_wick_ratio():
    detector = LiquiditySweepDetector(min_wick_ratio=0.5)
    # High swept but upper wick too small (large body)
    candle = {"open": 190.0, "high": 202.0, "low": 189.0, "close": 199.0}
    event = detector.detect_sweep(candle, key_high=200.0)
    assert event.detected is False

def test_invalid_candle_range():
    detector = LiquiditySweepDetector()
    candle = {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}
    event = detector.detect_sweep(candle, key_high=100.0)
    assert event.detected is False
    assert "Invalid or zero candle range" in event.reason

def test_no_key_levels_provided():
    detector = LiquiditySweepDetector()
    candle = {"open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0}
    event = detector.detect_sweep(candle)
    assert event.detected is False
