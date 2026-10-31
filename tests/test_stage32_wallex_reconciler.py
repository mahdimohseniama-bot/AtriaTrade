import pytest
from unittest.mock import MagicMock
from src.core.wallex_position_reconciler import WallexPositionReconciler

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    return adapter

def test_stage32_reconciliation_detects_orphans(mock_adapter):
    mock_adapter.get_open_orders.return_value = [
        {"order_id": "101"},
        {"order_id": "102"},
        {"order_id": "103"}
    ]
    reconciler = WallexPositionReconciler(mock_adapter)
    
    # Internal state only knows about 101
    res = reconciler.reconcile_open_orders(symbol="BTCUSDT", internal_order_ids=["101"])
    
    assert res["status"] == "synchronized"
    assert res["exchange_count"] == 3
    assert set(res["orphan_orders"]) == {"102", "103"}
    assert res["missing_on_exchange"] == []

def test_stage32_reconciliation_detects_missing_on_exchange(mock_adapter):
    mock_adapter.get_open_orders.return_value = [
        {"order_id": "101"}
    ]
    reconciler = WallexPositionReconciler(mock_adapter)
    
    # Internal state thinks 101 and 999 are open
    res = reconciler.reconcile_open_orders(symbol="BTCUSDT", internal_order_ids=["101", "999"])
    
    assert res["status"] == "synchronized"
    assert res["orphan_orders"] == []
    assert res["missing_on_exchange"] == ["999"]

def test_stage32_cancel_orphan_orders(mock_adapter):
    mock_adapter.cancel_order.return_value = {"status": "cancelled"}
    reconciler = WallexPositionReconciler(mock_adapter)
    
    result = reconciler.cancel_orphan_orders(symbol="BTCUSDT", orphan_ids=["102", "103"])
    assert result["cancelled"] == 2
    assert result["failed"] == 0
    assert mock_adapter.cancel_order.call_count == 2
