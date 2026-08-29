"""
Unit tests for Liquidity Void & Imbalance Rebalancing Engine (Capability 91)
"""
import pytest
from src.core.liquidity_void_engine import LiquidityVoidEngine, LiquidityVoid

def test_detect_bullish_displacement_void():
    engine = LiquidityVoidEngine(min_void_pct=1.0)
    # 100 to 110 is a 10% displacement
    void = engine.detect_void(
        symbol="BTCUSDT",
        candle_high=110.0,
        candle_low=100.0,
        candle_direction="BULLISH"
    )
    assert void is not None
    assert void.direction == "BULLISH_DISPLACEMENT"
    assert void.equilibrium_level == 105.0
    assert void.status == "OPEN"
    assert void.filled_ratio == 0.0

def test_detect_bearish_displacement_void():
    engine = LiquidityVoidEngine(min_void_pct=1.0)
    void = engine.detect_void(
        symbol="ETHUSDT",
        candle_high=200.0,
        candle_low=180.0,
        candle_direction="BEARISH"
    )
    assert void is not None
    assert void.direction == "BEARISH_DISPLACEMENT"
    assert void.equilibrium_level == 190.0
    assert void.top_price == 200.0

def test_small_candle_ignored():
    engine = LiquidityVoidEngine(min_void_pct=2.0)
    # Range 100 to 101 is 1% -> below 2% threshold
    void = engine.detect_void(
        symbol="BTCUSDT",
        candle_high=101.0,
        candle_low=100.0
    )
    assert void is None

def test_void_rebalancing_progress():
    engine = LiquidityVoidEngine(min_void_pct=1.0)
    void = engine.detect_void(
        symbol="BTCUSDT",
        candle_high=200.0,
        candle_low=100.0,
        candle_direction="BULLISH"
    )
    assert void is not None

    # Price rebalances down to 150 (50% filled)
    engine.update_rebalance_status(void, current_price=150.0)
    assert void.filled_ratio == 0.5
    assert void.status == "PARTIALLY_FILLED"

    # Price rebalances down to 100 (100% filled)
    engine.update_rebalance_status(void, current_price=100.0)
    assert void.filled_ratio == 1.0
    assert void.status == "FULLY_FILLED"

def test_active_magnet_targets():
    engine = LiquidityVoidEngine(min_void_pct=1.0)
    engine.detect_void(symbol="BTCUSDT", candle_high=110.0, candle_low=100.0, candle_direction="BULLISH")
    targets = engine.get_active_targets(symbol="BTCUSDT")
    assert len(targets) == 1
    assert targets[0]["equilibrium_50pct"] == 105.0
    assert targets[0]["full_fill_price"] == 100.0

def test_invalid_parameters_handling():
    engine = LiquidityVoidEngine()
    void = engine.detect_void(symbol="BTCUSDT", candle_high=100.0, candle_low=100.0)
    assert void is None
    void_neg = engine.detect_void(symbol="BTCUSDT", candle_high=100.0, candle_low=-5.0)
    assert void_neg is None
