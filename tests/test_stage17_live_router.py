import os
from unittest.mock import patch
from src.exchange.wallex_live_router import WallexLiveRouter

def test_stage17_router_dry_run_pipeline():
    print("[STAGE 17] TESTING DRY-RUN ROUTER PIPELINE...")

    router = WallexLiveRouter(dry_run=True, max_allowed_spread_pct=1.0)

    # Mock orderbook to isolate test logic
    mock_book = {
        "best_bid": 90000.0,
        "best_ask": 90200.0,
        "spread_pct": 0.22,
        "bid_volume_top5": 1000.0,
        "ask_volume_top5": 1000.0
    }

    with patch.object(router.fetcher, "fetch_orderbook", return_value=mock_book):
        signal = {
            "symbol": "TMNUSDT",
            "action": "BUY",
            "price": 90200.0,
            "quantity": 2.0  # Total = 180,400 TMN (> min 100,000 limit)
        }
        res = router.process_strategy_signal(signal)
        assert res["status"] == "COMPLETED", f"Expected COMPLETED, got {res}"
        assert res["mode"] == "DRY_RUN"
        assert res["executed_price"] == 90200.0
        print("[SUCCESS] Stage 17 Dry-Run Signal Execution Passed!")

def test_stage17_router_spread_rejection():
    print("[STAGE 17] TESTING SPREAD REJECTION GATE...")

    router = WallexLiveRouter(dry_run=True, max_allowed_spread_pct=0.3)

    mock_wide_book = {
        "best_bid": 90000.0,
        "best_ask": 91000.0,
        "spread_pct": 1.11,  # Exceeds 0.3%
        "bid_volume_top5": 1000.0,
        "ask_volume_top5": 1000.0
    }

    with patch.object(router.fetcher, "fetch_orderbook", return_value=mock_wide_book):
        signal = {
            "symbol": "TMNUSDT",
            "action": "BUY",
            "price": 91000.0,
            "quantity": 2.0
        }
        res = router.process_strategy_signal(signal)
        assert res["status"] == "REJECTED"
        assert res["reason"] == "SPREAD_EXCEEDS_THRESHOLD"
        print("[SUCCESS] Stage 17 High Spread Rejection Passed!")

def test_stage17_router_live_blocked_without_env():
    print("[STAGE 17] TESTING ROUTER UNINTENDED LIVE BLOCK...")

    os.environ.pop("ALLOW_WALLEX_LIVE", None)
    os.environ.pop("WALLEX_KILL_SWITCH", None)

    router = WallexLiveRouter(dry_run=False)
    signal = {
        "symbol": "TMNUSDT",
        "action": "BUY",
        "price": 90000.0,
        "quantity": 2.0
    }
    res = router.process_strategy_signal(signal)
    assert res["status"] == "BLOCKED"
    assert res["reason"] == "GUARD_PREFLIGHT_PREVENTED_EXECUTION"
    print("[SUCCESS] Stage 17 Live Blocking Safety Gate Passed!")

if __name__ == "__main__":
    test_stage17_router_dry_run_pipeline()
    test_stage17_router_spread_rejection()
    test_stage17_router_live_blocked_without_env()
    print("[SUCCESS] Stage 17 Live Router Passed!")
