import pytest
from src.core.breakeven_tp_orchestrator import BreakEvenTPOrchestrator, ManagedTrade, TakeProfitTarget


def test_buy_trade_partial_tp_and_breakeven():
    orchestrator = BreakEvenTPOrchestrator(auto_be_on_tp1=True)

    tps = [
        TakeProfitTarget(target_id=1, price=105.0, percentage_to_close=0.50),
        TakeProfitTarget(target_id=2, price=110.0, percentage_to_close=1.00),
    ]

    trade = ManagedTrade(
        trade_id="T001",
        symbol="BTCUSDT",
        direction="BUY",
        entry_price=100.0,
        current_size=2.0,
        stop_loss=95.0,
        take_profits=tps,
        fee_buffer_percent=0.001
    )

    # 1. بار اول قیمت به TP1 می‌رسد
    res1 = orchestrator.evaluate_price_update(trade, current_high=106.0, current_low=99.0)
    assert "TP1_HIT" in res1["events"]
    assert "MOVED_TO_BREAKEVEN" in res1["events"]
    assert res1["remaining_size"] == 1.0
    assert trade.is_breakeven is True
    # استاپ جدید = 100 * 1.001 = 100.1
    assert trade.stop_loss == 100.1
    assert res1["realized_pnl"] == 5.0  # (105 - 100) * 1.0

    # 2. بار دوم قیمت به TP2 می‌رسد
    res2 = orchestrator.evaluate_price_update(trade, current_high=111.0, current_low=102.0)
    assert "TP2_HIT" in res2["events"]
    assert res2["remaining_size"] == 0.0
    assert res2["realized_pnl"] == 15.0  # 5.0 + (110 - 100) * 1.0


def test_sell_trade_partial_tp_and_breakeven():
    orchestrator = BreakEvenTPOrchestrator(auto_be_on_tp1=True)

    tps = [
        TakeProfitTarget(target_id=1, price=95.0, percentage_to_close=0.50),
        TakeProfitTarget(target_id=2, price=90.0, percentage_to_close=1.00),
    ]

    trade = ManagedTrade(
        trade_id="T002",
        symbol="ETHUSDT",
        direction="SELL",
        entry_price=100.0,
        current_size=4.0,
        stop_loss=105.0,
        take_profits=tps,
        fee_buffer_percent=0.001
    )

    res1 = orchestrator.evaluate_price_update(trade, current_high=101.0, current_low=94.0)
    assert "TP1_HIT" in res1["events"]
    assert "MOVED_TO_BREAKEVEN" in res1["events"]
    assert res1["remaining_size"] == 2.0
    assert trade.is_breakeven is True
    # استاپ جدید = 100 * (1 - 0.001) = 99.9
    assert trade.stop_loss == 99.9
    assert res1["realized_pnl"] == 10.0  # (100 - 95) * 2.0


def test_no_tp_hit_sl_remains_intact():
    orchestrator = BreakEvenTPOrchestrator()
    tps = [TakeProfitTarget(target_id=1, price=110.0, percentage_to_close=0.5)]
    trade = ManagedTrade(
        trade_id="T003",
        symbol="SOLUSDT",
        direction="BUY",
        entry_price=100.0,
        current_size=1.0,
        stop_loss=95.0,
        take_profits=tps
    )

    res = orchestrator.evaluate_price_update(trade, current_high=105.0, current_low=98.0)
    assert len(res["events"]) == 0
    assert res["remaining_size"] == 1.0
    assert res["stop_loss"] == 95.0
    assert trade.is_breakeven is False
