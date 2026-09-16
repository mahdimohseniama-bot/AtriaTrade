import pytest
from src.core.fvg_detector import Candle
from src.core.smc_structure_engine import (
    SMCStructureEngine,
    OrderBlockType
)


def test_swing_highs_and_lows():
    engine = SMCStructureEngine(swing_lookback=1)
    candles = [
        Candle(open=10, high=12, low=9, close=11),
        Candle(open=11, high=15, low=10, close=14),  # Swing High at index 1
        Candle(open=14, high=13, low=8, close=9),    # Swing Low at index 2
        Candle(open=9, high=14, low=9, close=13),
    ]
    highs, lows = engine.find_swing_highs_lows(candles)
    assert (1, 15) in highs
    assert (2, 8) in lows


def test_bullish_order_block():
    engine = SMCStructureEngine()
    candles = [
        Candle(open=100, high=102, low=98, close=101),
        Candle(open=101, high=102, low=95, close=96),   # Bearish candle (OB candidate)
        Candle(open=96, high=112, low=96, close=110),   # Strong impulse up
        Candle(open=110, high=115, low=109, close=114),
    ]
    obs = engine.detect_order_blocks(candles)
    assert len(obs) >= 1
    bullish_obs = [ob for ob in obs if ob.ob_type == OrderBlockType.BULLISH]
    assert len(bullish_obs) == 1
    assert bullish_obs[0].candle_index == 1
    assert bullish_obs[0].low == 95
    assert bullish_obs[0].high == 102


def test_bearish_order_block():
    engine = SMCStructureEngine()
    candles = [
        Candle(open=100, high=102, low=98, close=100),
        Candle(open=100, high=108, low=99, close=107),  # Bullish candle (OB candidate)
        Candle(open=107, high=107, low=90, close=91),   # Strong impulse drop
        Candle(open=91, high=92, low=85, close=86),
    ]
    obs = engine.detect_order_blocks(candles)
    assert len(obs) >= 1
    bearish_obs = [ob for ob in obs if ob.ob_type == OrderBlockType.BEARISH]
    assert len(bearish_obs) == 1
    assert bearish_obs[0].candle_index == 1
    assert bearish_obs[0].high == 108
    assert bearish_obs[0].low == 99


def test_invalid_parameters():
    with pytest.raises(ValueError):
        SMCStructureEngine(swing_lookback=0)
