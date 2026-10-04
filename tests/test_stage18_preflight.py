import os
from unittest.mock import patch
from src.exchange.wallex_preflight import WallexPreflight

def test_stage18_preflight_not_ready_by_default():
    print("[STAGE 18] TESTING PREFLIGHT DEFAULT NOT_READY...")

    os.environ.pop("ALLOW_WALLEX_LIVE", None)
    os.environ.pop("WALLEX_KILL_SWITCH", None)
    os.environ.pop("WALLEX_API_KEY", None)
    os.environ.pop("WALLEX_API_SECRET", None)

    pf = WallexPreflight(symbol="TMNUSDT")

    with patch.object(pf.orderbook, "fetch_orderbook", return_value={"spread_pct": 0.2}):
        res = pf.run()

    assert res.status == "NOT_READY"
    assert "ALLOW_WALLEX_LIVE_DISABLED" in res.reasons
    print("[SUCCESS] Stage 18 Default Preflight NOT_READY Passed!")

def test_stage18_preflight_ready_when_env_ok():
    print("[STAGE 18] TESTING PREFLIGHT READY...")

    os.environ["ALLOW_WALLEX_LIVE"] = "1"
    os.environ["WALLEX_KILL_SWITCH"] = "0"
    os.environ["WALLEX_API_KEY"] = "fake_key"
    os.environ["WALLEX_API_SECRET"] = "fake_secret"

    pf = WallexPreflight(symbol="TMNUSDT", api_key="fake_key", api_secret="fake_secret")

    with patch.object(pf.orderbook, "fetch_orderbook", return_value={"spread_pct": 0.2}), \
         patch.object(pf, "_get_account_balances", return_value={"TMN": 1000000.0, "USDT": 10.0}):
        res = pf.run()

    assert res.status == "READY", f"Expected READY, got {res}"
    assert res.reasons == []
    print("[SUCCESS] Stage 18 Preflight READY Passed!")

def test_stage18_preflight_rejects_market_or_account_failure():
    print("[STAGE 18] TESTING PREFLIGHT MARKET/ACCOUNT FAILURE...")

    os.environ["ALLOW_WALLEX_LIVE"] = "1"
    os.environ["WALLEX_KILL_SWITCH"] = "0"
    os.environ["WALLEX_API_KEY"] = "fake_key"
    os.environ["WALLEX_API_SECRET"] = "fake_secret"

    pf = WallexPreflight(symbol="TMNUSDT", api_key="fake_key", api_secret="fake_secret")

    with patch.object(pf.orderbook, "fetch_orderbook", return_value=None), \
         patch.object(pf, "_get_account_balances", return_value=None):
        res = pf.run()

    assert res.status == "NOT_READY"
    assert "ORDERBOOK_UNAVAILABLE" in res.reasons
    assert "ACCOUNT_UNAVAILABLE" in res.reasons
    print("[SUCCESS] Stage 18 Market/Account Failure Handling Passed!")

if __name__ == "__main__":
    test_stage18_preflight_not_ready_by_default()
    test_stage18_preflight_ready_when_env_ok()
    test_stage18_preflight_rejects_market_or_account_failure()
    print("[SUCCESS] Stage 18 Preflight Passed!")
