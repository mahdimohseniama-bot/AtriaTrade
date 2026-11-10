import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_execution_engine import WallexLiveExecutionEngine

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.create_order.return_value = {"order_id": "WALLEX_12345", "status": "FILLED"}
    return adapter

@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.evaluate_pre_trade_safety.return_value = {
        "allowed": True,
        "reason": "APPROVED",
        "effective_price": 100.05
    }
    return coordinator

@pytest.fixture
def mock_sizer():
    sizer = MagicMock()
    sizer.compute_size.return_value = {
        "allowed": True,
        "reason": "SIZE_CALCULATED_SUCCESSFULLY",
        "size": 0.1,
        "notional": 10.0
    }
    return sizer

def test_execution_engine_success(mock_adapter, mock_coordinator, mock_sizer):
    engine = WallexLiveExecutionEngine(mock_adapter, mock_coordinator, mock_sizer)
    orderbook = {"bids": [[100.0, 1.0]], "asks": [[100.1, 1.0]]}
    
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        account_balance=15.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        orderbook=orderbook,
        reference_price=100.0
    )
    
    assert res["status"] == "EXECUTED"
    assert res["quantity"] == 0.1
    assert res["exchange_response"]["order_id"] == "WALLEX_12345"
    mock_adapter.create_order.assert_called_once()

def test_execution_engine_blocked_by_sizer(mock_adapter, mock_coordinator, mock_sizer):
    mock_sizer.compute_size.return_value = {
        "allowed": False,
        "reason": "BALANCE_BELOW_MIN_NOTIONAL",
        "size": 0.0
    }
    engine = WallexLiveExecutionEngine(mock_adapter, mock_coordinator, mock_sizer)
    
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        account_balance=2.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        orderbook={},
        reference_price=100.0
    )
    
    assert res["status"] == "REJECTED"
    assert res["stage"] == "POSITION_SIZER"
    mock_adapter.create_order.assert_not_called()

def test_execution_engine_blocked_by_coordinator(mock_adapter, mock_coordinator, mock_sizer):
    mock_coordinator.evaluate_pre_trade_safety.return_value = {
        "allowed": False,
        "reason": "EXCESSIVE_SLIPPAGE"
    }
    engine = WallexLiveExecutionEngine(mock_adapter, mock_coordinator, mock_sizer)
    
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        account_balance=15.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        orderbook={},
        reference_price=100.0
    )
    
    assert res["status"] == "REJECTED"
    assert res["stage"] == "SAFETY_COORDINATOR"
    mock_adapter.create_order.assert_not_called()
