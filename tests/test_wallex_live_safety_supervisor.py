import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_safety_supervisor import WallexLiveSafetySupervisor

@pytest.fixture
def supervisor():
    mock_orchestrator = MagicMock()
    mock_orchestrator.emergency_mgr = MagicMock()
    mock_orchestrator.reconciler = MagicMock()
    return WallexLiveSafetySupervisor(
        orchestrator=mock_orchestrator,
        heartbeat_timeout_sec=5.0,
        max_heartbeat_misses=3
    )

def test_supervisor_healthy_heartbeat(supervisor):
    supervisor.record_heartbeat(timestamp=100.0)
    health = supervisor.evaluate_health(current_ts=102.0)
    assert health["healthy"] is True
    assert health["status"] == "HEALTHY"

def test_supervisor_heartbeat_warning(supervisor):
    supervisor.record_heartbeat(timestamp=100.0)
    # Elapsed 6s > 5s timeout, misses = 1 (< 3)
    health = supervisor.evaluate_health(current_ts=106.0)
    assert health["healthy"] is False
    assert health["status"] == "HEARTBEAT_WARNING"
    supervisor.orchestrator.emergency_mgr.trigger_emergency_halt.assert_not_called()

def test_supervisor_triggers_emergency_on_max_misses(supervisor):
    supervisor.record_heartbeat(timestamp=100.0)
    # Elapsed 16s > 15s (3 misses)
    health = supervisor.evaluate_health(current_ts=116.0)
    assert health["healthy"] is False
    assert health["status"] == "EMERGENCY_HALTED"
    supervisor.orchestrator.emergency_mgr.trigger_emergency_halt.assert_called_once()

def test_supervisor_periodic_drift_scan_halt(supervisor):
    supervisor.orchestrator.reconciler.reconcile.return_value = {
        "has_drift": True,
        "drifts": {"BTC": 0.05}
    }
    res = supervisor.trigger_periodic_drift_scan({"BTC": 0.1}, {"BTC": 0.15})
    assert res["status"] == "DRIFT_BREACH"
    supervisor.orchestrator.emergency_mgr.trigger_emergency_halt.assert_called_with("SUPERVISOR_DETECTED_POSITION_DRIFT")
