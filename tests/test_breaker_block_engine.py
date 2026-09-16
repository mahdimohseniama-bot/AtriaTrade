import pytest
from src.core.breaker_block_engine import BreakerBlockEngine, BlockRole


def test_bullish_ob_inverts_to_bearish_breaker():
    engine = BreakerBlockEngine()
    # Bullish OB [100-105] broken by close at 99.5 (below bottom)
    res = engine.check_invalidation(
        block_role=BlockRole.BULLISH_OB,
        block_top=105.0,
        block_bottom=100.0,
        break_close=99.5
    )
    assert res is not None
    assert res.new_role == BlockRole.BEARISH_BREAKER
    assert res.original_role == BlockRole.BULLISH_OB
    assert res.mid_price == 102.5


def test_bearish_ob_inverts_to_bullish_breaker():
    engine = BreakerBlockEngine()
    # Bearish OB [200-205] broken by close at 206 (above top)
    res = engine.check_invalidation(
        block_role=BlockRole.BEARISH_OB,
        block_top=205.0,
        block_bottom=200.0,
        break_close=206.0
    )
    assert res is not None
    assert res.new_role == BlockRole.BULLISH_BREAKER
    assert res.mid_price == 202.5


def test_bullish_ob_intact_no_breaker():
    engine = BreakerBlockEngine()
    # Close inside the block (no break below bottom)
    res = engine.check_invalidation(
        block_role=BlockRole.BULLISH_OB,
        block_top=105.0,
        block_bottom=100.0,
        break_close=102.0
    )
    assert res is None


def test_bearish_ob_intact_no_breaker():
    engine = BreakerBlockEngine()
    # Close inside the block (no break above top)
    res = engine.check_invalidation(
        block_role=BlockRole.BEARISH_OB,
        block_top=205.0,
        block_bottom=200.0,
        break_close=203.0
    )
    assert res is None


def test_min_close_beyond_threshold_blocks_weak_break():
    engine = BreakerBlockEngine(min_close_beyond=1.0)
    # Close at 99.8 is only 0.2 beyond bottom (100.0), threshold is 1.0 -> NOT broken
    res = engine.check_invalidation(
        block_role=BlockRole.BULLISH_OB,
        block_top=105.0,
        block_bottom=100.0,
        break_close=99.8
    )
    assert res is None
    # Close at 98.5 is 1.5 beyond bottom -> broken
    res2 = engine.check_invalidation(
        block_role=BlockRole.BULLISH_OB,
        block_top=105.0,
        block_bottom=100.0,
        break_close=98.5
    )
    assert res2 is not None
    assert res2.new_role == BlockRole.BEARISH_BREAKER


def test_invalid_block_prices_raise_error():
    engine = BreakerBlockEngine()
    with pytest.raises(ValueError):
        engine.check_invalidation(
            block_role=BlockRole.BULLISH_OB,
            block_top=100.0,
            block_bottom=105.0,  # Invalid: bottom > top
            break_close=99.0
        )


def test_retest_validation():
    engine = BreakerBlockEngine()
    breaker = engine.check_invalidation(
        block_role=BlockRole.BULLISH_OB,
        block_top=105.0,
        block_bottom=100.0,
        break_close=99.0
    )
    # Short retest inside the zone is valid
    assert engine.is_retest_valid(breaker, 103.0, "SHORT") is True
    # Long retest on a bearish breaker is invalid
    assert engine.is_retest_valid(breaker, 103.0, "LONG") is False
    # Retest outside the zone is invalid
    assert engine.is_retest_valid(breaker, 110.0, "SHORT") is False
