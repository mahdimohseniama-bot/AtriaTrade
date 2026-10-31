import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_engine import WallexLiveExecutionEngine
from src.core.wallex_circuit_breaker import WallexCircuitBreaker
from src.core.wallex_order_guard import WallexOrderGuard

@pytest.fixture
def mock_setup():
    syncer = MagicMock()
    syncer.has_sufficient_balance.return_value = True
    syncer.get_balance.return_value = 1000.0
    
    executor = MagicMock()
    executor.place_order.return_value = {"order_id": "W-12345", "status": "FILLED"}
    circuit_breaker = WallexCircuitBreaker(max_consecutive_errors=2, cooldown_seconds=10.0)
    order_guard = WallexOrderGuard(min_order_value_usdt=5.0, max_spread_pct=1.0)
    
    engine = WallexLiveExecutionEngine(
        executor=executor,
        balance_syncer=syncer,
        circuit_breaker=circuit_breaker,
        order_guard=order_guard
    )
    return engine, executor, circuit_breaker

def test_stage31_engine_blocks_on_circuit_breaker(mock_setup):
    engine, _, circuit_breaker = mock_setup
    circuit_breaker.record_failure("Err 1")
    circuit_breaker.record_failure("Err 2")
    
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        amount=0.001,
        price=60000.0,
        best_bid=60000.0,
        best_ask=60010.0
    )
    assert res["status"] == "rejected"
    assert res["reason"] == "circuit_breaker_active"

def test_stage31_engine_blocks_on_guard_violation(mock_setup):
    engine, _, _ = mock_setup
    # Wide spread: Bid 60000, Ask 62000 (~3.3% > 1.0%)
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        amount=0.001,
        price=60000.0,
        best_bid=60000.0,
        best_ask=62000.0
    )
    assert res["status"] == "rejected"
    assert "Spread too wide" in res["reason"]

def test_stage31_engine_successful_execution(mock_setup):
    engine, executor, _ = mock_setup
    res = engine.execute_live_order(
        symbol="BTCUSDT",
        side="BUY",
        amount=0.001,
        price=60000.0,
        best_bid=60000.0,
        best_ask=60050.0
    )
    assert res["status"] == "executed"
    assert res["order_result"]["order_id"] == "W-12345"
    executor.place_order.assert_called_once()
