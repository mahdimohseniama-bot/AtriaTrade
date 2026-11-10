import pytest
from unittest.mock import Mock
from src.core.live_position_reconciler import LivePositionReconciler

def test_reconciliation_syncs_tracker():
    # Setup
    mock_tracker = Mock()
    mock_session = Mock()
    mock_fetch = Mock(return_value=[{"symbol": "BTCIRT", "amount": 0.05}])
    
    # Session returns successful positions
    mock_session.request_with_retry.return_value = {
        "success": True, 
        "data": [{"symbol": "BTCIRT", "amount": 0.05}]
    }
    
    reconciler = LivePositionReconciler(mock_session, mock_tracker)
    
    # Act
    res = reconciler.reconcile_live_positions(mock_fetch)
    
    # Assert
    assert res["synced"] is True
    mock_tracker.update_position.assert_called_with(symbol="BTCIRT", amount=0.05)

def test_reconciliation_handles_failure():
    mock_tracker = Mock()
    mock_session = Mock()
    mock_session.request_with_retry.return_value = {"success": False, "error": "API_DOWN"}
    
    reconciler = LivePositionReconciler(mock_session, mock_tracker)
    res = reconciler.reconcile_live_positions(lambda: [])
    
    assert res["synced"] is False
    mock_tracker.update_position.assert_not_called()
