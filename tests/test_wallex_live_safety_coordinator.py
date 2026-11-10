import pytest
from src.core.wallex_live_safety_coordinator import WallexLiveSafetyCoordinator
from src.core.wallex_live_safety_supervisor import WallexLiveSafetySupervisor
from src.core.wallex_orderbook_liquidity_guard import WallexOrderBookLiquidityGuard
from src.core.wallex_live_execution_tolerance_guard import WallexLiveExecutionToleranceGuard

@pytest.fixture
def coordinator():
    sup = WallexLiveSafetySupervisor(heartbeat_timeout_sec=5.0)
    liq = WallexOrderBookLiquidityGuard(max_allowed_slippage_pct=0.01)
    tol = WallexLiveExecutionToleranceGuard(max_price_drift_pct=0.005, max_signal_age_sec=5.0)
    return WallexLiveSafetyCoordinator(supervisor=sup, liquidity_guard=liq, tolerance_guard=tol)

def test_coordinator_blocked_by_supervisor_unhealthy(coordinator):
    # Heartbeat was never pulsed or timed out
    ob = {"asks": [[100.0, 1.0]], "bids": [[99.0, 1.0]]}
    res = coordinator.evaluate_pre_order("USDTIRT", "BUY", 0.5, 100.0, 100.0, ob, 100.0, 106.0)
    assert res["permitted"] is False
    assert res["stage"] == "SUPERVISOR"

def test_coordinator_blocked_by_tolerance_guard(coordinator):
    coordinator.supervisor.pulse_heartbeat(100.0)
    ob = {"asks": [[102.0, 1.0]], "bids": [[99.0, 1.0]]}
    # Signal price was 100, now market jumped to 102 (2% drift > 0.5%)
    res = coordinator.evaluate_pre_order("USDTIRT", "BUY", 0.5, 100.0, 102.0, ob, 100.0, 101.0)
    assert res["permitted"] is False
    assert res["stage"] == "TOLERANCE_GUARD"
    assert res["reason"] == "ADVERSE_PRICE_DRIFT"

def test_coordinator_blocked_by_liquidity_guard(coordinator):
    coordinator.supervisor.pulse_heartbeat(100.0)
    # Orderbook has thin liquidity (only 0.1 size available at best price, required 1.0)
    ob = {"asks": [[100.0, 0.1], [105.0, 1.0]], "bids": [[99.0, 1.0]]}
    res = coordinator.evaluate_pre_order("USDTIRT", "BUY", 1.0, 100.0, 100.0, ob, 100.0, 101.0)
    assert res["permitted"] is False
    assert res["stage"] == "LIQUIDITY_GUARD"

def test_coordinator_approval_success(coordinator):
    coordinator.supervisor.pulse_heartbeat(100.0)
    ob = {"asks": [[100.1, 2.0]], "bids": [[99.9, 2.0]]}
    res = coordinator.evaluate_pre_order("USDTIRT", "BUY", 0.5, 100.0, 100.1, ob, 100.0, 101.0)
    assert res["permitted"] is True
    assert res["stage"] == "APPROVED"
    assert res["reason"] == "ALL_SAFETY_CHECKS_PASSED"
