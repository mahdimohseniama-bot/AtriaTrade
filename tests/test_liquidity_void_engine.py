import pytest
from src.core.liquidity_void_engine import (
    LiquidityVoidEngine,
    LiquidityVoid,
    VoidType,
    VoidStatus,
)


def test_detect_bullish_liquidity_void():
    engine = LiquidityVoidEngine(expansion_multiplier=2.0)
    # Average body = 10, Current body = 25 (Open 100 -> Close 125, High 126, Low 99)
    res = engine.detect_void(
        open_price=100.0,
        high_price=126.0,
        low_price=99.0,
        close_price=125.0,
        avg_body_size=10.0,
        void_id="v_bull_1"
    )
    assert res is not None
    assert res.void_type == VoidType.BULLISH_VOID
    assert res.top_price == 125.0
    assert res.bottom_price == 100.0
    assert res.ce_price == 112.5
    assert res.expansion_range == 25.0
    assert res.status == VoidStatus.ACTIVE


def test_detect_bearish_liquidity_void():
    engine = LiquidityVoidEngine(expansion_multiplier=2.0)
    # Average body = 5, Current body = 15 (Open 115 -> Close 100, High 116, Low 98)
    res = engine.detect_void(
        open_price=115.0,
        high_price=116.0,
        low_price=98.0,
        close_price=100.0,
        avg_body_size=5.0,
        void_id="v_bear_1"
    )
    assert res is not None
    assert res.void_type == VoidType.BEARISH_VOID
    assert res.top_price == 115.0
    assert res.bottom_price == 100.0
    assert res.ce_price == 107.5
    assert res.status == VoidStatus.ACTIVE


def test_no_void_on_normal_volatility():
    engine = LiquidityVoidEngine(expansion_multiplier=2.0)
    # Average body = 10, Current body = 12 (< 20 required)
    res = engine.detect_void(
        open_price=100.0,
        high_price=114.0,
        low_price=99.0,
        close_price=112.0,
        avg_body_size=10.0
    )
    assert res is None


def test_bullish_void_rebalance_lifecycle():
    engine = LiquidityVoidEngine()
    void = LiquidityVoid(
        void_id="v1",
        void_type=VoidType.BULLISH_VOID,
        top_price=120.0,
        bottom_price=100.0,
        ce_price=110.0,
        expansion_range=20.0,
        status=VoidStatus.ACTIVE
    )

    # 1. Price retraces slightly (Low 115) -> still ACTIVE
    status = engine.update_void_status(void, current_high=122.0, current_low=115.0)
    assert status == VoidStatus.ACTIVE

    # 2. Price hits 50% CE level (Low 108) -> PARTIALLY_FILLED
    status = engine.update_void_status(void, current_high=118.0, current_low=108.0)
    assert status == VoidStatus.PARTIALLY_FILLED

    # 3. Price fully sweeps to bottom (Low 99) -> FULLY_REBALANCED
    status = engine.update_void_status(void, current_high=105.0, current_low=99.0)
    assert status == VoidStatus.FULLY_REBALANCED


def test_bearish_void_rebalance_lifecycle():
    engine = LiquidityVoidEngine()
    void = LiquidityVoid(
        void_id="v2",
        void_type=VoidType.BEARISH_VOID,
        top_price=100.0,
        bottom_price=80.0,
        ce_price=90.0,
        expansion_range=20.0,
        status=VoidStatus.ACTIVE
    )

    # 1. Small rally (High 85) -> ACTIVE
    status = engine.update_void_status(void, current_high=85.0, current_low=79.0)
    assert status == VoidStatus.ACTIVE

    # 2. Reaches CE (High 92) -> PARTIALLY_FILLED
    status = engine.update_void_status(void, current_high=92.0, current_low=84.0)
    assert status == VoidStatus.PARTIALLY_FILLED

    # 3. Fully rebalanced (High 101) -> FULLY_REBALANCED
    status = engine.update_void_status(void, current_high=101.0, current_low=88.0)
    assert status == VoidStatus.FULLY_REBALANCED


def test_invalid_parameters_raise_errors():
    with pytest.raises(ValueError):
        LiquidityVoidEngine(expansion_multiplier=0.8)

    engine = LiquidityVoidEngine(expansion_multiplier=2.0)
    with pytest.raises(ValueError):
        engine.detect_void(100.0, 90.0, 110.0, 95.0, avg_body_size=10.0)

    with pytest.raises(ValueError):
        engine.detect_void(100.0, 110.0, 90.0, 105.0, avg_body_size=-5.0)

    void = LiquidityVoid("v", VoidType.BULLISH_VOID, 120.0, 100.0, 110.0, 20.0)
    with pytest.raises(ValueError):
        engine.update_void_status(void, current_high=100.0, current_low=110.0)
