import pytest
from unittest.mock import MagicMock
from src.core.wallex_recovery_manager import WallexRecoveryManager, RecoveryState

class MockExchangeAdapter:
    def __init__(self, open_orders=None, balances=None, healthy=True):
        self._open_orders = open_orders or []
        self._balances = balances or {"USDT": 150.0, "BTC": 0.01}
        self.healthy = healthy
        self.cancelled_orders = []

    def get_open_orders(self, symbol="BTCUSDT"):
        if not self.healthy:
            raise ConnectionError("Wallex API Unreachable")
        return self._open_orders

    def get_balances(self):
        if not self.healthy:
            raise ConnectionError("Wallex API Unreachable")
        return self._balances

    def cancel_order(self, order_id):
        self.cancelled_orders.append(order_id)
        return {"status": "CANCELED", "id": order_id}

def test_stage37_recovery_clean_state_sync():
    adapter = MockExchangeAdapter(
        open_orders=[{"id": "ORD-1", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": 0.001}],
        balances={"USDT": 200.0, "BTC": 0.05}
    )
    recovery = WallexRecoveryManager(exchange_adapter=adapter)
    
    # Internal state holds ORD-1 as known active order
    report = recovery.recover_and_sync(known_internal_orders=["ORD-1"])
    
    assert report.is_clean_sync is True
    assert report.state == RecoveryState.SYNCED
    assert report.orphan_orders_found == 0
    assert report.cancelled_orphans == 0
    assert report.balances["USDT"] == 200.0

def test_stage37_recovery_orphan_orders_cancellation():
    # Wallex has ORD-1 (known) and ORD-99 (unknown / orphan from previous crash)
    adapter = MockExchangeAdapter(
        open_orders=[
            {"id": "ORD-1", "symbol": "BTCUSDT", "side": "BUY", "price": 60000.0, "quantity": 0.001},
            {"id": "ORD-99", "symbol": "BTCUSDT", "side": "SELL", "price": 65000.0, "quantity": 0.001}
        ]
    )
    recovery = WallexRecoveryManager(exchange_adapter=adapter)
    
    report = recovery.recover_and_sync(known_internal_orders=["ORD-1"], cancel_orphans=True)
    
    assert report.is_clean_sync is False
    assert report.state == RecoveryState.RESOLVED_ORPHANS
    assert report.orphan_orders_found == 1
    assert "ORD-99" in report.orphan_order_ids
    assert "ORD-99" in adapter.cancelled_orders

def test_stage37_recovery_unreachable_triggers_safe_mode():
    adapter = MockExchangeAdapter(healthy=False)
    recovery = WallexRecoveryManager(exchange_adapter=adapter)
    
    report = recovery.recover_and_sync(known_internal_orders=["ORD-1"])
    
    assert report.is_clean_sync is False
    assert report.state == RecoveryState.SAFE_MODE
    assert report.error_message is not None
    assert "Wallex API Unreachable" in report.error_message
