"""
Unit tests for Multi-Timeframe Fractal Breaker Block Engine (Capability 92)
"""
import pytest
from src.core.breaker_block_engine import BreakerBlockEngine, BreakerBlock

def test_identify_bullish_breaker_success():
    engine = BreakerBlockEngine(max_mitigations=2)
    # Down-candle OB was 100-105. Price swept low to 95, then exploded above 105 to 110
    breaker = engine.identify_bullish_breaker(
        symbol="BTCUSDT",
        timeframe="15m",
        failed_ob_high=105.0,
        failed_ob_low=100.0,
        liquidity_sweep_low=95.0,
        breakout_price=110.0
    )
    assert breaker is not None
    assert breaker.breaker_type == "BULLISH_BREAKER"
    assert breaker.status == "ACTIVE"
    assert breaker.mitigation_count == 0

def test_identify_bearish_breaker_success():
    engine = BreakerBlockEngine(max_mitigations=2)
    # Up-candle OB was 200-205. Price swept high to 210, then dumped below 200 to 195
    breaker = engine.identify_bearish_breaker(
        symbol="ETHUSDT",
        timeframe="1h",
        failed_ob_high=205.0,
        failed_ob_low=200.0,
        liquidity_sweep_high=210.0,
        breakout_price=195.0
    )
    assert breaker is not None
    assert breaker.breaker_type == "BEARISH_BREAKER"
    assert breaker.status == "ACTIVE"

def test_breaker_invalid_parameters():
    engine = BreakerBlockEngine()
    # Breakout price didn't cross the OB
    breaker = engine.identify_bullish_breaker(
        symbol="BTCUSDT",
        timeframe="15m",
        failed_ob_high=105.0,
        failed_ob_low=100.0,
        liquidity_sweep_low=95.0,
        breakout_price=103.0  # Not broken above 105
    )
    assert breaker is None

def test_breaker_retest_and_mitigation():
    engine = BreakerBlockEngine(max_mitigations=2)
    breaker = engine.identify_bullish_breaker(
        symbol="BTCUSDT",
        timeframe="15m",
        failed_ob_high=105.0,
        failed_ob_low=100.0,
        liquidity_sweep_low=95.0,
        breakout_price=110.0
    )
    assert breaker is not None

    # First retest inside zone (102.0)
    engine.evaluate_retest(breaker, test_price=102.0)
    assert breaker.mitigation_count == 1
    assert breaker.status == "ACTIVE"

    # Second retest inside zone -> fully mitigated
    engine.evaluate_retest(breaker, test_price=104.0)
    assert breaker.mitigation_count == 2
    assert breaker.status == "MITIGATED"
    assert breaker.is_mitigated is True

def test_breaker_invalidation():
    engine = BreakerBlockEngine()
    breaker = engine.identify_bullish_breaker(
        symbol="BTCUSDT",
        timeframe="15m",
        failed_ob_high=105.0,
        failed_ob_low=100.0,
        liquidity_sweep_low=95.0,
        breakout_price=110.0
    )
    assert breaker is not None

    # Price violently breaks below zone (98.0 < 100.0)
    engine.evaluate_retest(breaker, test_price=98.0)
    assert breaker.status == "INVALIDATED"

def test_get_active_breakers_filtering():
    engine = BreakerBlockEngine()
    engine.identify_bullish_breaker("BTCUSDT", "15m", 105.0, 100.0, 95.0, 110.0)
    engine.identify_bullish_breaker("ETHUSDT", "1h", 205.0, 200.0, 190.0, 215.0)

    btc_15m = engine.get_active_breakers(symbol="BTCUSDT", timeframe="15m")
    assert len(btc_15m) == 1
    assert btc_15m[0]["timeframe"] == "15m"

    eth_15m = engine.get_active_breakers(symbol="ETHUSDT", timeframe="15m")
    assert len(eth_15m) == 0
