import pytest
from unittest.mock import MagicMock
from src.core.live_capital_guardrail import LiveCapitalGuardrail
from src.core.live_circuit_breaker_emergency_manager import LiveCircuitBreakerEmergencyManager
from src.core.wallex_live_safety_orchestrator import WallexLiveSafetyOrchestrator

@pytest.fixture
def orchestrator():
    mock_exec_mgr = MagicMock()
    mock_reconciler = MagicMock()
    
    # Default behavior: no drift
    mock_reconciler.reconcile.return_value = {"has_drift": False, "drifts": {}}

    guardrail = LiveCapitalGuardrail(max_order_ratio=0.25, min_reserve_ratio=0.10, min_notional_irt=100000.0)
    emergency_mgr = LiveCircuitBreakerEmergencyManager(max_consecutive_errors=3)
    
    return WallexLiveSafetyOrchestrator(
        execution_manager=mock_exec_mgr,
        reconciler=mock_reconciler,
        guardrail=guardrail,
        emergency_manager=emergency_mgr
    )

def test_pre_flight_approved(orchestrator):
    res = orchestrator.pre_flight_order_check(
        symbol="BTC_IRT",
        side="buy",
        price=1000000.0,
        quantity=0.5, # 500,000 IRT
        client_order_id="ORD_SAFE_1001",
        total_balance=10000000.0,
        available_balance=9000000.0,
        local_positions={"BTC": 0.1},
        exchange_positions={"BTC": 0.1}
    )
    assert res["approved"] is True
    assert res["stage"] == "PASSED"
    assert res["notional"] == 500000.0

def test_pre_flight_blocks_when_breaker_active(orchestrator):
    orchestrator.emergency_mgr.trigger_emergency_halt("EMERGENCY_TEST_HALT")
    res = orchestrator.pre_flight_order_check(
        symbol="BTC_IRT",
        side="buy",
        price=1000000.0,
        quantity=0.5,
        client_order_id="ORD_BLOCK_001",
        total_balance=10000000.0,
        available_balance=9000000.0,
        local_positions={"BTC": 0.1},
        exchange_positions={"BTC": 0.1}
    )
    assert res["approved"] is False
    assert res["stage"] == "CIRCUIT_BREAKER"

def test_pre_flight_blocks_on_position_drift(orchestrator):
    # Simulate drift detected by reconciler
    orchestrator.reconciler.reconcile.return_value = {
        "has_drift": True,
        "drifts": {"BTC": {"local": 0.1, "exchange": 0.2, "drift": 0.1}}
    }
    
    res = orchestrator.pre_flight_order_check(
        symbol="BTC_IRT",
        side="buy",
        price=1000000.0,
        quantity=0.5,
        client_order_id="ORD_BLOCK_002",
        total_balance=10000000.0,
        available_balance=9000000.0,
        local_positions={"BTC": 0.1},
        exchange_positions={"BTC": 0.2}
    )
    assert res["approved"] is False
    assert res["stage"] == "POSITION_RECONCILER"
    assert res["reason"] == "POSITION_DRIFT_EXCEEDED"

def test_pre_flight_blocks_on_capital_violation(orchestrator):
    res = orchestrator.pre_flight_order_check(
        symbol="BTC_IRT",
        side="buy",
        price=10000.0,
        quantity=1.0, # 10,000 < 100,000 min notional
        client_order_id="ORD_BLOCK_003",
        total_balance=10000000.0,
        available_balance=9000000.0,
        local_positions={"BTC": 0.1},
        exchange_positions={"BTC": 0.1}
    )
    assert res["approved"] is False
    assert res["stage"] == "CAPITAL_GUARDRAIL"
    assert res["reason"] == "BELOW_MIN_NOTIONAL"
