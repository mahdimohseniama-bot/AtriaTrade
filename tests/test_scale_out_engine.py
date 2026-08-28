import pytest
from src.core.scale_out_engine import ScaleOutEngine


def test_scale_out_invalid_inputs():
    engine = ScaleOutEngine()
    res = engine.evaluate_scale_out(entry_price=0, current_price=100, current_qty=1.0)
    assert res["should_scale_out"] is False
    assert res["reason"] == "INVALID_INPUTS"


def test_scale_out_no_target_hit():
    engine = ScaleOutEngine()
    # سود ۱٪ است در حالی که اولین تارگت ۲٪ است
    res = engine.evaluate_scale_out(entry_price=100, current_price=101, current_qty=1.0, side="BUY")
    assert res["should_scale_out"] is False
    assert res["reason"] == "NO_NEW_TARGET_HIT"
    assert res["current_pnl_pct"] == pytest.approx(1.0)


def test_scale_out_first_target_hit_long():
    engine = ScaleOutEngine()
    # سود ۳٪ (بیشتر از تارگت ۲٪)
    res = engine.evaluate_scale_out(entry_price=100, current_price=103, current_qty=10.0, side="BUY")
    assert res["should_scale_out"] is True
    assert res["target_index"] == 0
    assert res["close_qty"] == pytest.approx(3.3)


def test_scale_out_subsequent_target():
    engine = ScaleOutEngine()
    # تارگت اول قبلاً اجرا شده، حالا سود ۶٪ رسیده و باید تارگت دوم فعال شود
    res = engine.evaluate_scale_out(
        entry_price=100,
        current_price=106,
        current_qty=6.7,
        side="BUY",
        executed_target_indices=[0],
    )
    assert res["should_scale_out"] is True
    assert res["target_index"] == 1
    assert res["target_profit_pct"] == 5.0


def test_scale_out_short_position():
    engine = ScaleOutEngine()
    # پوزیشن شورت: قیمت از ۱۰۰ به ۹۷.۵ افت کرده (۲.۵٪ سود)
    res = engine.evaluate_scale_out(
        entry_price=100,
        current_price=97.5,
        current_qty=2.0,
        side="SELL",
    )
    assert res["should_scale_out"] is True
    assert res["target_index"] == 0
    assert res["current_pnl_pct"] == pytest.approx(2.5)
