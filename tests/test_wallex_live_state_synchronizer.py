import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_state_synchronizer import WallexLiveStateSynchronizer

@pytest.fixture
def sync_setup():
    mock_exchange = MagicMock()
    mock_exchange.get_balances.return_value = {
        "IRT": {"available": 50000000.0, "locked": 10000000.0},
        "BTC": {"available": 0.15, "locked": 0.05}
    }
    synchronizer = WallexLiveStateSynchronizer(exchange_adapter=mock_exchange, max_order_age_sec=60.0)
    return synchronizer, mock_exchange

def test_perform_sync_healthy(sync_setup):
    synchronizer, mock_exchange = sync_setup
    mock_exchange.get_open_orders.return_value = [
        {"id": "ord_101", "symbol": "BTC_IRT", "timestamp": 1000.0}
    ]
    res = synchronizer.perform_sync(current_ts=1020.0)
    assert res["status"] == "SYNCED"
    assert res["balances"]["IRT"] == 60000000.0
    assert res["balances"]["BTC"] == 0.2
    assert res["active_orders_count"] == 1
    assert len(res["stale_orders"]) == 0

def test_perform_sync_detects_stale_orders(sync_setup):
    synchronizer, mock_exchange = sync_setup
    mock_exchange.get_open_orders.return_value = [
        {"id": "ord_fresh", "symbol": "BTC_IRT", "timestamp": 1000.0},
        {"id": "ord_old", "symbol": "BTC_IRT", "timestamp": 900.0} # 120s old > 60s
    ]
    res = synchronizer.perform_sync(current_ts=1020.0)
    assert res["active_orders_count"] == 1
    assert "ord_fresh" in synchronizer.synchronized_orders
    assert "ord_old" not in synchronizer.synchronized_orders
    assert res["stale_orders"] == ["ord_old"]

def test_cancel_stale_orders(sync_setup):
    synchronizer, mock_exchange = sync_setup
    mock_exchange.cancel_order.side_effect = lambda oid: {"success": True, "id": oid}
    cancelled = synchronizer.cancel_stale_orders(["ord_old_1", "ord_old_2"])
    assert cancelled == ["ord_old_1", "ord_old_2"]
    assert mock_exchange.cancel_order.call_count == 2
