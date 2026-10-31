import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_orchestrator import WallexLiveOrchestrator

@pytest.fixture
def orchestrator_mocks():
    engine = MagicMock()
    heartbeat = MagicMock()
    limiter = MagicMock()
    reconciler = MagicMock()
    
    # Defaults: clean and ready
    heartbeat.ping.return_value = {"is_healthy": True, "latency_ms": 120.0}
    heartbeat.should_pause_trading.return_value = False
    limiter.acquire.return_value = True
    reconciler.reconcile_open_orders.return_value = {
        "status": "synchronized",
        "orphan_orders": [],
        "missing_on_exchange": []
    }
    engine.execute_order.return_value = {"status": "filled", "order_id": "9988"}
    
    orch = WallexLiveOrchestrator(
        execution_engine=engine,
        heartbeat_monitor=heartbeat,
        rate_limiter=limiter,
        reconciler=reconciler
    )
    return orch, engine, heartbeat, limiter, reconciler

def test_stage35_orchestrator_skips_on_rate_limit(orchestrator_mocks):
    orch, engine, _, limiter, _ = orchestrator_mocks
    limiter.acquire.return_value = False
    
    res = orch.execute_live_cycle(
        symbol="BTCUSDT",
        signal={"action": "BUY", "amount": 0.001, "price": 60000.0},
        active_order_ids=[]
    )
    
    assert res["status"] == "skipped"
    assert res["reason"] == "rate_limited"
    engine.execute_order.assert_not_called()

def test_stage35_orchestrator_skips_on_unhealthy_network(orchestrator_mocks):
    orch, engine, heartbeat, _, _ = orchestrator_mocks
    heartbeat.ping.return_value = {"is_healthy": False, "reason": "endpoint_unresponsive"}
    
    res = orch.execute_live_cycle(
        symbol="BTCUSDT",
        signal={"action": "BUY", "amount": 0.001, "price": 60000.0},
        active_order_ids=[]
    )
    
    assert res["status"] == "skipped"
    assert res["reason"] == "network_unhealthy"
    engine.execute_order.assert_not_called()

def test_stage35_orchestrator_cancels_orphans_and_executes(orchestrator_mocks):
    orch, engine, _, _, reconciler = orchestrator_mocks
    reconciler.reconcile_open_orders.return_value = {
        "status": "synchronized",
        "orphan_orders": ["orphan_123"],
        "missing_on_exchange": []
    }
    
    res = orch.execute_live_cycle(
        symbol="BTCUSDT",
        signal={"action": "BUY", "amount": 0.001, "price": 60000.0},
        active_order_ids=[]
    )
    
    reconciler.cancel_orphan_orders.assert_called_once_with(symbol="BTCUSDT", orphan_ids=["orphan_123"])
    engine.execute_order.assert_called_once_with(
        symbol="BTCUSDT",
        side="BUY",
        amount=0.001,
        price=60000.0
    )
    assert res["status"] == "executed"
