import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.order_manager import OrderSide, OrderStatus

def test_paper_runner_initialization():
    runner = PaperTradingLiveRunner(initial_balance=5000.0)
    summary = runner.get_session_summary()
    assert summary["initial_balance"] == 5000.0
    assert summary["current_balance"] == 5000.0
    assert summary["trades_count"] == 0
    assert summary["roi_pct"] == 0.0

def test_paper_order_execution():
    runner = PaperTradingLiveRunner(initial_balance=10000.0)
    order = runner.execute_paper_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        price=50000.0,
        quantity=0.1,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    assert order is not None
    assert order.status == OrderStatus.FILLED.value
    assert runner.session.current_balance == 5000.0
    assert runner.session.trades_count == 1
    
    summary = runner.get_session_summary()
    assert summary["trades_count"] == 1
    assert len(runner.trade_history) == 1

def test_paper_candle_processing():
    runner = PaperTradingLiveRunner(initial_balance=10000.0)
    candle = {
        "open": 50000.0,
        "high": 50500.0,
        "low": 49800.0,
        "close": 50200.0,
        "volume": 120.0
    }
    res = runner.process_candle("BTCUSDT", candle)
    assert res is None
