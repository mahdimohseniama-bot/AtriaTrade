from src.core.stage12_orchestrator_spread_gate import Stage12OrchestratorSpreadGate
from src.core.spread_fee_filter import SpreadFeeFilter

def test_stage12_spread_gate():
    print("[STAGE 12] ORCHESTRATOR SPREAD GATE TEST STARTING...")

    flt = SpreadFeeFilter(max_spread_pct=0.30, taker_fee_pct=0.2)
    orch = Stage12OrchestratorSpreadGate(spread_filter=flt)

    d1 = orch.should_open_position(best_bid=1000000.0, best_ask=1001500.0)
    assert d1["allowed"] is True, f"Expected allowed but got {d1}"
    assert d1["reason"] == "OK"
    assert d1["spread_pct"] == 0.15

    d2 = orch.should_open_position(best_bid=1000000.0, best_ask=1005000.0)
    assert d2["allowed"] is False, f"Expected blocked but got {d2}"
    assert d2["reason"] == "SPREAD_TOO_HIGH"

    d3 = orch.should_open_position(best_bid=0.0, best_ask=1000.0)
    assert d3["allowed"] is False, f"Expected blocked but got {d3}"
    assert d3["reason"] == "INVALID_PRICES"

    print("[SUCCESS] Stage 12 Orchestrator Spread Gate Passed!")

if __name__ == "__main__":
    test_stage12_spread_gate()
