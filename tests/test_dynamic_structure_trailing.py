import pytest
from src.core.dynamic_structure_trailing import DynamicStructureTrailing, TrailingState


def test_atr_trailing_buy_ratchet():
    engine = DynamicStructureTrailing(mode="ATR")
    state = TrailingState(
        symbol="BTCUSDT",
        direction="BUY",
        current_sl=100.0,
        highest_price=105.0,
        lowest_price=99.0,
        atr_multiplier=2.0
    )

    # کندل با سقف 110 و ATR = 2.0 -> proposed_sl = 110 - (2 * 2) = 106.0
    res1 = engine.update_trailing_stop(state, current_high=110.0, current_low=104.0, current_atr=2.0)
    assert res1["trail_moved"] is True
    assert res1["new_sl"] == 106.0
    assert state.highest_price == 110.0

    # کندل نزولی اصلاحی با سقف 108 -> استاپ نباید عقب برود (باید روی 106 ثابت بماند)
    res2 = engine.update_trailing_stop(state, current_high=108.0, current_low=103.0, current_atr=2.0)
    assert res2["trail_moved"] is False
    assert res2["new_sl"] == 106.0


def test_atr_trailing_sell_ratchet():
    engine = DynamicStructureTrailing(mode="ATR")
    state = TrailingState(
        symbol="ETHUSDT",
        direction="SELL",
        current_sl=100.0,
        highest_price=101.0,
        lowest_price=95.0,
        atr_multiplier=2.0
    )

    # قیمت کف جدید 90 می‌زند و ATR = 2.0 -> proposed_sl = 90 + (2 * 2) = 94.0
    res1 = engine.update_trailing_stop(state, current_high=96.0, current_low=90.0, current_atr=2.0)
    assert res1["trail_moved"] is True
    assert res1["new_sl"] == 94.0

    # قیمت پولبک می‌زند به سمت بالا با کف 92 -> استاپ نباید بالا برود
    res2 = engine.update_trailing_stop(state, current_high=95.0, current_low=92.0, current_atr=2.0)
    assert res2["trail_moved"] is False
    assert res2["new_sl"] == 94.0


def test_structure_trailing():
    engine = DynamicStructureTrailing(mode="STRUCTURE")
    state = TrailingState(
        symbol="SOLUSDT",
        direction="BUY",
        current_sl=100.0,
        highest_price=110.0,
        lowest_price=98.0,
        buffer_percent=0.01  # 1%
    )

    # سووینگ جدید تشکیل شده در 108 -> استاپ جدید = 108 * (1 - 0.01) = 106.92
    res = engine.update_trailing_stop(state, current_high=115.0, current_low=107.0, swing_level=108.0)
    assert res["trail_moved"] is True
    assert res["new_sl"] == 106.92
