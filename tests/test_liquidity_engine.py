import pytest
from src.core.fvg_detector import Candle
from src.core.liquidity_engine import (
    LiquidityEngine,
    LiquidityType,
    SweepType
)


def test_detect_equal_highs_and_lows():
    engine = LiquidityEngine(tolerance_pct=0.001)
    candles = [
        Candle(open=100, high=105.00, low=98, close=102),  # i = 0
        Candle(open=102, high=103.00, low=95.00, close=97),# i = 1
        Candle(open=97, high=105.05, low=96, close=104),   # i = 2 (EQH with 0)
        Candle(open=104, high=104.00, low=95.02, close=100),# i = 3 (EQL with 1)
    ]
    pools = engine.detect_equal_highs_lows(candles)
    eqh = [p for p in pools if p.pool_type == LiquidityType.EQUAL_HIGHS]
    eql = [p for p in pools if p.pool_type == LiquidityType.EQUAL_LOWS]

    assert len(eqh) >= 1
    assert len(eql) >= 1
    assert eqh[0].candle_indices == [0, 2]
    assert eql[0].candle_indices == [1, 3]


def test_detect_bearish_sweep():
    engine = LiquidityEngine()
    key_resistance = 100.0
    candles = [
        Candle(open=95, high=99, low=94, close=98),
        Candle(open=98, high=103, low=97, close=99),  # Swept 100, closed at 99
        Candle(open=99, high=99, low=92, close=93),
    ]
    sweeps = engine.detect_sweeps(candles, key_level=key_resistance, is_high_level=True)
    assert len(sweeps) == 1
    assert sweeps[0].sweep_type == SweepType.BEARISH_SWEEP
    assert sweeps[0].swept_level == 100.0
    assert sweeps[0].wick_penetration == 3.0
    assert sweeps[0].candle_index == 1


def test_detect_bullish_sweep():
    engine = LiquidityEngine()
    key_support = 50.0
    candles = [
        Candle(open=55, high=56, low=51, close=52),
        Candle(open=52, high=54, low=47, close=51),  # Swept 50, closed at 51
        Candle(open=51, high=58, low=51, close=57),
    ]
    sweeps = engine.detect_sweeps(candles, key_level=key_support, is_high_level=False)
    assert len(sweeps) == 1
    assert sweeps[0].sweep_type == SweepType.BULLISH_SWEEP
    assert sweeps[0].swept_level == 50.0
    assert sweeps[0].wick_penetration == 3.0
    assert sweeps[0].candle_index == 1


def test_invalid_tolerance():
    with pytest.raises(ValueError):
        LiquidityEngine(tolerance_pct=0.0)
