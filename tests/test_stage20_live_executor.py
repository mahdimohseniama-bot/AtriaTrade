import os
from unittest.mock import patch, MagicMock
from src.exchange.wallex_live_executor import WallexLiveExecutor
from src.exchange.wallex_micro_plan import MicroOrderPlan

def test_stage20_dry_run_execution():
    print("[STAGE 20] TESTING DRY-RUN EXECUTION...")
    os.environ.pop("ALLOW_WALLEX_LIVE", None)
    os.environ["WALLEX_KILL_SWITCH"] = "0"

    executor = WallexLiveExecutor()
    plan = MicroOrderPlan(
        symbol="TMNUSDT",
        side="BUY",
        target_price=60000.0,
        quantity=2.0,
        total_value=120000.0,
        stop_loss=58800.0,
        take_profit=62400.0,
        is_valid=True
    )

    result = executor.execute_plan(plan)
    assert result["status"] == "DRY_RUN_SUCCESS"
    assert result["order_id"] == "sim_wallex_1001"
    print("[SUCCESS] Stage 20 Dry-Run Execution Passed!")

def test_stage20_rejects_invalid_plan():
    print("[STAGE 20] TESTING REJECT INVALID PLAN...")
    executor = WallexLiveExecutor()
    invalid_plan = MicroOrderPlan(
        symbol="TMNUSDT",
        side="BUY",
        target_price=0.0,
        quantity=0.0,
        total_value=0.0,
        stop_loss=0.0,
        take_profit=0.0,
        is_valid=False,
        rejection_reason="BELOW_MIN_NOTIONAL"
    )

    result = executor.execute_plan(invalid_plan)
    assert result["status"] == "REJECTED"
    assert result["reason"] == "BELOW_MIN_NOTIONAL"
    print("[SUCCESS] Stage 20 Invalid Plan Rejection Passed!")

def test_stage20_live_order_mock_success():
    print("[STAGE 20] TESTING LIVE ORDER MOCK SUCCESS...")
    os.environ["ALLOW_WALLEX_LIVE"] = "1"
    os.environ["WALLEX_KILL_SWITCH"] = "0"
    os.environ["WALLEX_API_KEY"] = "mock_key"
    os.environ["WALLEX_API_SECRET"] = "mock_secret"

    executor = WallexLiveExecutor(api_key="mock_key", api_secret="mock_secret")
    plan = MicroOrderPlan(
        symbol="TMNUSDT",
        side="BUY",
        target_price=60000.0,
        quantity=2.0,
        total_value=120000.0,
        stop_loss=58800.0,
        take_profit=62400.0,
        is_valid=True
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": {"id": "w_live_998877"}}

    with patch.object(executor.session, "post", return_value=mock_resp):
        res = executor.execute_plan(plan)

    assert res["status"] == "LIVE_PLACED"
    assert res["order_id"] == "w_live_998877"
    print("[SUCCESS] Stage 20 Live Order Mock Passed!")

if __name__ == "__main__":
    test_stage20_dry_run_execution()
    test_stage20_rejects_invalid_plan()
    test_stage20_live_order_mock_success()
    print("[SUCCESS] Stage 20 Live Executor Passed!")
