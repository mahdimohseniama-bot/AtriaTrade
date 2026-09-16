"""
Unit tests for Fair Value Gap Tracker Engine (Capability 93)
"""

import pytest
from src.core.fvg_tracker_engine import FVGTrackerEngine, FVGType, FVGStatus


def test_bullish_fvg_detection():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    # Candle 0: High = 100, Low = 90
    # Candle 1: High = 115, Low = 98 (Big up move)
    # Candle 2: High = 120, Low = 105 (Low 105 > High 100 -> FVG [100, 105])
    candles = [
        {"open": 92, "high": 100, "low": 90, "close": 98, "timestamp": 1000},
        {"open": 98, "high": 115, "low": 98, "close": 114, "timestamp": 2000},
        {"open": 114, "high": 120, "low": 105, "close": 118, "timestamp": 3000},
    ]
    gaps = engine.scan_gaps(candles)
    assert len(gaps) == 1
    fvg = gaps[0]
    assert fvg.gap_type == FVGType.BULLISH
    assert fvg.bottom_price == 100.0
    assert fvg.top_price == 105.0
    assert fvg.midpoint == 102.5
    assert fvg.status == FVGStatus.UNTOUCHED


def test_bearish_fvg_detection():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    # Candle 0: High = 200, Low = 190
    # Candle 1: High = 192, Low = 175 (Big down move)
    # Candle 2: High = 180, Low = 170 (High 180 < Low 190 -> FVG [180, 190])
    candles = [
        {"open": 198, "high": 200, "low": 190, "close": 192, "timestamp": 1000},
        {"open": 191, "high": 192, "low": 175, "close": 176, "timestamp": 2000},
        {"open": 176, "high": 180, "low": 170, "close": 172, "timestamp": 3000},
    ]
    gaps = engine.scan_gaps(candles)
    assert len(gaps) == 1
    fvg = gaps[0]
    assert fvg.gap_type == FVGType.BEARISH
    assert fvg.bottom_price == 180.0
    assert fvg.top_price == 190.0
    assert fvg.midpoint == 185.0
    assert fvg.status == FVGStatus.UNTOUCHED


def test_no_gap_when_overlapping():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    # Overlapping candles
    candles = [
        {"open": 100, "high": 105, "low": 95, "close": 102},
        {"open": 102, "high": 108, "low": 100, "close": 107},
        {"open": 107, "high": 110, "low": 103, "close": 105},  # Low 103 < High 105 -> No Bull FVG
    ]
    gaps = engine.scan_gaps(candles)
    assert len(gaps) == 0


def test_bullish_fvg_partial_and_full_fill():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    candles = [
        {"index": 0, "open": 92, "high": 100, "low": 90, "close": 98},
        {"index": 1, "open": 98, "high": 115, "low": 98, "close": 114},
        {"index": 2, "open": 114, "high": 120, "low": 110, "close": 118},  # FVG [100, 110] (gap_size=10)
    ]
    engine.scan_gaps(candles)
    assert len(engine.gaps) == 1

    # Future candle partially dipping to 105 (fills 50%)
    future_1 = [{"index": 3, "open": 118, "high": 119, "low": 105, "close": 108}]
    engine.update_mitigation(future_1)
    gap = engine.gaps[0]
    assert gap.status == FVGStatus.PARTIALLY_FILLED
    assert gap.filled_ratio == pytest.approx(0.5, 0.01)

    # Future candle penetrating to 99 (completely fills and crosses below 100)
    future_2 = [{"index": 4, "open": 108, "high": 110, "low": 98, "close": 102}]
    engine.update_mitigation(future_2)
    assert gap.status == FVGStatus.FULLY_FILLED
    assert gap.filled_ratio == 1.0


def test_bearish_fvg_inversion():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    candles = [
        {"index": 0, "open": 198, "high": 200, "low": 190, "close": 192},
        {"index": 1, "open": 191, "high": 192, "low": 175, "close": 176},
        {"index": 2, "open": 176, "high": 180, "low": 170, "close": 172},  # Bearish FVG [180, 190]
    ]
    engine.scan_gaps(candles)

    # Candle spikes up and closes above 190 -> Inversion
    future = [{"index": 3, "open": 172, "high": 195, "low": 171, "close": 193}]
    engine.update_mitigation(future)
    gap = engine.gaps[0]
    assert gap.status == FVGStatus.INVERTED
    assert gap.filled_ratio == 1.0


def test_get_active_gaps_filtering():
    engine = FVGTrackerEngine(min_gap_size_pct=0.001)
    candles = [
        {"index": 0, "open": 92, "high": 100, "low": 90, "close": 98},
        {"index": 1, "open": 98, "high": 115, "low": 98, "close": 114},
        {"index": 2, "open": 114, "high": 120, "low": 110, "close": 118},
    ]
    engine.scan_gaps(candles)
    assert len(engine.get_active_gaps(unmitigated_only=True)) == 1

    # Mitigate fully
    future = [{"index": 3, "open": 118, "high": 119, "low": 95, "close": 96}]
    engine.update_mitigation(future)
    assert len(engine.get_active_gaps(unmitigated_only=True)) == 0
    assert len(engine.get_active_gaps(unmitigated_only=False)) == 1
