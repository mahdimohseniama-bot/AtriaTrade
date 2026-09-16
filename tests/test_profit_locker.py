import pytest
from src.core.profit_locker import ProfitLocker, PositionProfitTracker


def test_profit_locker_buy_tier1_and_tier2():
    locker = ProfitLocker()
    tracker = PositionProfitTracker(
        position_id="POS_BUY_1",
        entry_price=100.0,
        size=2.0,
        direction="BUY",
        tier1_threshold=100.0,
        tier1_lock_ratio=0.50,
        tier2_threshold=200.0,
        tier2_lock_ratio=0.75
    )

    # 1. حرکت قیمت به 160 -> سود = (160 - 100) * 2 = 120 (ورود به Tier 1)
    res1 = locker.evaluate_price(tracker, current_price=160.0)
    assert res1["current_pnl"] == 120.0
    assert res1["peak_pnl"] == 120.0
    assert res1["locked_profit_floor"] == 60.0  # 50% of 120
    assert res1["should_close"] is False

    # 2. حرکت قیمت به 220 -> سود = (220 - 100) * 2 = 240 (ورود به Tier 2)
    res2 = locker.evaluate_price(tracker, current_price=220.0)
    assert res2["current_pnl"] == 240.0
    assert res2["peak_pnl"] == 240.0
    assert res2["locked_profit_floor"] == 180.0  # 75% of 240
    assert res2["should_close"] is False

    # 3. ریزش قیمت به 185 -> سود = (185 - 100) * 2 = 170 (< 180 Locked Floor)
    res3 = locker.evaluate_price(tracker, current_price=185.0)
    assert res3["current_pnl"] == 170.0
    assert res3["should_close"] is True
    assert res3["reason"] == "PROFIT_PROTECTION_TRIGGERED"


def test_profit_locker_sell_scenario():
    locker = ProfitLocker()
    tracker = PositionProfitTracker(
        position_id="POS_SELL_1",
        entry_price=100.0,
        size=1.0,
        direction="SELL",
        tier1_threshold=50.0,
        tier1_lock_ratio=0.50
    )

    # سود با ریزش به 40 -> سود = (100 - 40) * 1 = 60
    res1 = locker.evaluate_price(tracker, current_price=40.0)
    assert res1["current_pnl"] == 60.0
    assert res1["locked_profit_floor"] == 30.0  # 50% of 60
    assert res1["should_close"] is False

    # بازگشت قیمت به 75 -> سود = (100 - 75) * 1 = 25 (< 30)
    res2 = locker.evaluate_price(tracker, current_price=75.0)
    assert res2["current_pnl"] == 25.0
    assert res2["should_close"] is True
    assert res2["reason"] == "PROFIT_PROTECTION_TRIGGERED"
