"""
Unit tests for SMC Institutional Order Flow & Composite Signal Engine (Capability 90)
"""
import pytest
from src.core.smc_composite_engine import SMCCompositeEngine

def test_high_confidence_bullish_composite():
    engine = SMCCompositeEngine(min_confidence_score=60.0)
    # Range 100 to 200, Price at 120 (Discount), Bullish FVG, Bullish OB, OTE aligned
    signal = engine.generate_signal(
        symbol="BTCUSDT",
        current_price=120.0,
        range_high=200.0,
        range_low=100.0,
        fvg_detected=True,
        fvg_direction="BULLISH",
        ob_detected=True,
        ob_direction="BULLISH",
        ote_aligned=True,
        liquidity_swept=True
    )
    assert signal.direction == "BUY"
    assert signal.confidence == "HIGH"
    assert signal.score >= 80.0
    assert signal.stop_loss < signal.entry_price
    assert signal.take_profit > signal.entry_price
    assert "Bullish Order Block mitigation" in signal.confluences

def test_high_confidence_bearish_composite():
    engine = SMCCompositeEngine(min_confidence_score=60.0)
    # Range 100 to 200, Price at 180 (Premium), Bearish FVG, Bearish OB
    signal = engine.generate_signal(
        symbol="ETHUSDT",
        current_price=180.0,
        range_high=200.0,
        range_low=100.0,
        fvg_detected=True,
        fvg_direction="BEARISH",
        ob_detected=True,
        ob_direction="BEARISH",
        liquidity_swept=True
    )
    assert signal.direction == "SELL"
    assert signal.confidence == "HIGH"
    assert signal.score >= 80.0
    assert signal.stop_loss > signal.entry_price
    assert signal.take_profit < signal.entry_price

def test_signal_rejection_due_to_zone_conflict():
    engine = SMCCompositeEngine()
    # Bullish triggers but price is deep in Extreme Premium (190) -> Long not allowed
    signal = engine.generate_signal(
        symbol="BTCUSDT",
        current_price=190.0,
        range_high=200.0,
        range_low=100.0,
        fvg_detected=True,
        fvg_direction="BULLISH",
        ob_detected=True,
        ob_direction="BULLISH"
    )
    assert signal.direction == "NEUTRAL"
    assert signal.confidence == "REJECTED"
    assert "Contradictory directional bias" in signal.rejection_reason

def test_low_confidence_score():
    engine = SMCCompositeEngine(min_confidence_score=70.0)
    # Only Discount zone (25 pts), no other confluences
    signal = engine.generate_signal(
        symbol="SOLUSDT",
        current_price=120.0,
        range_high=200.0,
        range_low=100.0
    )
    assert signal.direction == "BUY"
    assert signal.confidence == "LOW"
    assert signal.score < 70.0

def test_invalid_parameters_rejection():
    engine = SMCCompositeEngine()
    signal = engine.generate_signal(
        symbol="BTCUSDT",
        current_price=-10.0,
        range_high=100.0,
        range_low=200.0
    )
    assert signal.confidence == "REJECTED"
    assert signal.rejection_reason == "Invalid market parameters"

def test_breaker_and_liquidity_confluence_addition():
    engine = SMCCompositeEngine()
    signal = engine.generate_signal(
        symbol="BTCUSDT",
        current_price=110.0,
        range_high=200.0,
        range_low=100.0,
        breaker_confirmed=True,
        liquidity_swept=True
    )
    assert signal.direction == "BUY"
    assert "Breaker/Mitigation Block confirmation" in signal.confluences
    assert "Session / Key Liquidity Sweep completed" in signal.confluences
