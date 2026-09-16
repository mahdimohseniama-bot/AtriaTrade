import pytest
from src.core.fvg_detector import FVGDetector, Candle, FVGType


def test_bullish_fvg_detection():
    detector = FVGDetector(min_gap_percent=0.1)
    candles = [
        Candle(open=100, high=105, low=99, close=104),   # C1: High = 105
        Candle(open=104, high=120, low=103, close=119),  # C2: Big impulse
        Candle(open=119, high=125, low=110, close=122),  # C3: Low = 110 (110 > 105)
    ]
    fvgs = detector.detect_fvgs(candles)
    assert len(fvgs) == 1
    assert fvgs[0].gap_type == FVGType.BULLISH
    assert fvgs[0].bottom_price == 105
    assert fvgs[0].top_price == 110
    assert fvgs[0].gap_size == 5.0


def test_bearish_fvg_detection():
    detector = FVGDetector(min_gap_percent=0.1)
    candles = [
        Candle(open=200, high=202, low=190, close=191),  # C1: Low = 190
        Candle(open=191, high=192, low=170, close=172),  # C2: Big drop
        Candle(open=172, high=180, low=168, close=175),  # C3: High = 180 (180 < 190)
    ]
    fvgs = detector.detect_fvgs(candles)
    assert len(fvgs) == 1
    assert fvgs[0].gap_type == FVGType.BEARISH
    assert fvgs[0].top_price == 190
    assert fvgs[0].bottom_price == 180
    assert fvgs[0].gap_size == 10.0


def test_no_fvg_when_overlapping():
    detector = FVGDetector()
    candles = [
        Candle(open=100, high=105, low=99, close=104),
        Candle(open=104, high=108, low=103, close=107),
        Candle(open=107, high=110, low=104, close=109),  # Low 104 <= High 105
    ]
    fvgs = detector.detect_fvgs(candles)
    assert len(fvgs) == 0


def test_mitigation_check():
    detector = FVGDetector()
    candles = [
        Candle(open=100, high=105, low=99, close=104),
        Candle(open=104, high=120, low=103, close=119),
        Candle(open=119, high=125, low=110, close=122),
    ]
    fvgs = detector.detect_fvgs(candles)
    fvg = fvgs[0]

    future_candles_not_mitigated = [
        Candle(open=122, high=130, low=115, close=128),
    ]
    assert detector.check_mitigation(fvg, future_candles_not_mitigated) is False

    future_candles_mitigated = [
        Candle(open=122, high=124, low=102, close=106),
    ]
    assert detector.check_mitigation(fvg, future_candles_mitigated) is True
