import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_reconciliation_engine import WallexLiveReconciliationEngine

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.get_balances.return_value = {"USDT": 15.5}
    adapter.get_open_orders.return_value = [{"id": "ORD_1"}, {"id": "ORD_2"}]
    return adapter

def test_reconciliation_balance_synced(mock_adapter):
    reconciler = WallexLiveReconciliationEngine(mock_adapter)
    res = reconciler.reconcile_balances(local_balance=15.5, currency="USDT")
    assert res["synced"] is True
    assert res["status"] == "SYNCED"
    assert res["discrepancy"] == 0.0

def test_reconciliation_balance_mismatch(mock_adapter):
    reconciler = WallexLiveReconciliationEngine(mock_adapter)
    res = reconciler.reconcile_balances(local_balance=20.0, currency="USDT")
    assert res["synced"] is False
    assert res["status"] == "BALANCE_MISMATCH"
    assert res["discrepancy"] == 4.5

def test_reconciliation_open_orders_aligned(mock_adapter):
    reconciler = WallexLiveReconciliationEngine(mock_adapter)
    res = reconciler.reconcile_open_orders(local_open_order_ids=["ORD_1", "ORD_2"], symbol="BTCUSDT")
    assert res["synced"] is True
    assert res["status"] == "ORDERS_ALIGNED"
    assert len(res["local_orphans"]) == 0
    assert len(res["remote_orphans"]) == 0

def test_reconciliation_open_orders_drift(mock_adapter):
    reconciler = WallexLiveReconciliationEngine(mock_adapter)
    res = reconciler.reconcile_open_orders(local_open_order_ids=["ORD_1"], symbol="BTCUSDT")
    assert res["synced"] is False
    assert res["status"] == "ORDERS_MISMATCH"
    assert "ORD_2" in res["remote_orphans"]
