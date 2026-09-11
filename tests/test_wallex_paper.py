import pytest
from src.adapters.wallex_paper import WallexPaperAdapter


def test_wallex_paper_initial_state():
    adapter = WallexPaperAdapter(initial_balance_usdt=100.0)
    assert adapter.balance_usdt == 100.0
    assert len(adapter.positions) == 0
    assert len(adapter.order_history) == 0


def test_wallex_paper_open_close_simulation(monkeypatch):
    adapter = WallexPaperAdapter(initial_balance_usdt=100.0, fee_rate=0.001)

    # شبیه‌سازی دریافت قیمت برای ایزوله‌سازی تست واحد
    monkeypatch.setattr(adapter, "get_latest_price", lambda sym: 50000.0)

    pos = adapter.open_position(
        symbol="BTCUSDT",
        side="LONG",
        amount_usdt=20.0,
        leverage=2,
        stop_loss=48000.0,
        take_profit=54000.0,
    )

    assert pos["entry_price"] == 50000.0
    assert pos["status"] == "OPEN"
    assert adapter.balance_usdt < 80.0  # 100 - (20 + کارمزد)

    # شبیه‌سازی قیمت خروج سودده (۵۲,۰۰۰ دلار -> ۴٪ رشد بدون اهرم، ۸٪ با اهرم ۲)
    monkeypatch.setattr(adapter, "get_latest_price", lambda sym: 52000.0)
    closed = adapter.close_position(pos["id"])

    assert closed["status"] == "CLOSED"
    assert closed["pnl_usdt"] > 0
    assert adapter.balance_usdt > 100.0
