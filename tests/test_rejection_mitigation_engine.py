import pytest
from src.core.rejection_mitigation_engine import RejectionMitigationEngine, BlockType


def test_bearish_rejection_block():
    engine = RejectionMitigationEngine(min_wick_ratio=0.5)
    # Candle: Open 100, High 120, Low 98, Close 102 (Body 100-102, Upper Wick 18, Range 22 -> ~81% upper wick)
    res = engine.detect_rejection_block(open_price=100.0, high_price=120.0, low_price=98.0, close_price=102.0)
    assert res is not None
    assert res.block_type == BlockType.BEARISH_REJECTION
    assert res.wick_start == 102.0
    assert res.wick_extreme == 120.0


def test_bullish_rejection_block():
    engine = RejectionMitigationEngine(min_wick_ratio=0.5)
    # Candle: Open 115, High 116, Low 95, Close 114 (Body 114-115, Lower Wick 19, Range 21 -> ~90% lower wick)
    res = engine.detect_rejection_block(open_price=115.0, high_price=116.0, low_price=95.0, close_price=114.0)
    assert res is not None
    assert res.block_type == BlockType.BULLISH_REJECTION
    assert res.wick_start == 114.0
    assert res.wick_extreme == 95.0


def test_no_rejection_for_balanced_candle():
    engine = RejectionMitigationEngine(min_wick_ratio=0.5)
    # Balanced body candle (Range 10, Body 8 from 96 to 104, upper wick 1, lower wick 1 -> ratio 0.1)
    res = engine.detect_rejection_block(open_price=96.0, high_price=105.0, low_price=95.0, close_price=104.0)
    assert res is None


def test_bearish_mitigation_block():
    engine = RejectionMitigationEngine()
    # Failure swing confirmed, OB [100-105] broken downwards at 98.0
    res = engine.detect_mitigation_block(
        is_failure_swing=True,
        block_top=105.0,
        block_bottom=100.0,
        break_close=98.0,
        direction="BEARISH"
    )
    assert res is not None
    assert res.block_type == BlockType.BEARISH_MITIGATION
    assert res.mid_price == 102.5


def test_bullish_mitigation_block():
    engine = RejectionMitigationEngine()
    # Failure swing confirmed, OB [100-105] broken upwards at 108.0
    res = engine.detect_mitigation_block(
        is_failure_swing=True,
        block_top=105.0,
        block_bottom=100.0,
        break_close=108.0,
        direction="BULLISH"
    )
    assert res is not None
    assert res.block_type == BlockType.BULLISH_MITIGATION
    assert res.mid_price == 102.5


def test_mitigation_ignored_if_not_failure_swing():
    engine = RejectionMitigationEngine()
    res = engine.detect_mitigation_block(
        is_failure_swing=False,
        block_top=105.0,
        block_bottom=100.0,
        break_close=98.0,
        direction="BEARISH"
    )
    assert res is None


def test_mitigation_invalid_levels_raises_error():
    engine = RejectionMitigationEngine()
    with pytest.raises(ValueError):
        engine.detect_mitigation_block(
            is_failure_swing=True,
            block_top=90.0,
            block_bottom=100.0,  # Invalid: top < bottom
            break_close=85.0,
            direction="BEARISH"
        )
