import pytest
from unittest.mock import Mock
from src.core.live_execution_manager import LiveExecutionManager

def test_execution_blocked_by_risk():
    # Setup mocks
    mock_pipeline = Mock()
    mock_risk = Mock()
    # Risk manager blocks the order
    mock_risk.validate_order.return_value = {"permitted": False, "reason": "DAILY_LOSS_EXCEEDED"}
    
    manager = LiveExecutionManager(pipeline=mock_pipeline, risk_manager=mock_risk)
    
    res = manager.execute_with_guard(
        client_order_id="TEST_001",
        symbol="BTCIRT",
        side="BUY",
        price=500000000.0,
        quantity=0.01,
        exchange_order_func=lambda x: x
    )
    
    assert res["status"] == "REJECTED_BY_RISK"
    assert res["reason"] == "DAILY_LOSS_EXCEEDED"
    # Pipeline should never be called
    mock_pipeline.submit_resilient_order.assert_not_called()

def test_execution_allowed_by_risk():
    mock_pipeline = Mock()
    mock_risk = Mock()
    # Risk manager approves
    mock_risk.validate_order.return_value = {"permitted": True}
    mock_pipeline.submit_resilient_order.return_value = {"status": "SUBMITTED"}
    
    manager = LiveExecutionManager(pipeline=mock_pipeline, risk_manager=mock_risk)
    
    res = manager.execute_with_guard(
        client_order_id="TEST_002",
        symbol="BTCIRT",
        side="BUY",
        price=500000000.0,
        quantity=0.01,
        exchange_order_func=lambda x: x
    )
    
    assert res["status"] == "SUBMITTED"
    mock_pipeline.submit_resilient_order.assert_called_once()
