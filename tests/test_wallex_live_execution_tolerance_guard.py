import pytest
from src.core.wallex_live_execution_tolerance_guard import WallexLiveExecutionToleranceGuard

@pytest.fixture
def guard():
    return WallexLiveExecutionToleranceGuard(max_price_drift_pct=0.005, max_signal_age_sec=5.0)

def test_signal_expired(guard):
    res = guard.validate_execution_price("BUY", 100.0, 100.1, signal_timestamp=100.0, current_timestamp=106.0)
    assert res["allowed"] is False
    assert res["reason"] == "SIGNAL_EXPIRED"

def test_invalid_prices(guard):
    res = guard.validate_execution_price("BUY", 0.0, 100.0, signal_timestamp=100.0, current_timestamp=101.0)
    assert res["allowed"] is False
    assert res["reason"] == "INVALID_PRICE_VALUES"

def test_acceptable_price_drift_buy(guard):
    # Buy signal at 100, market is at 100.2 (0.2% drift <= 0.5% allowed)
    res = guard.validate_execution_price("BUY", 100.0, 100.2, signal_timestamp=100.0, current_timestamp=102.0)
    assert res["allowed"] is True
    assert res["reason"] == "APPROVED"
    assert res["drift_pct"] == pytest.approx(0.002, abs=1e-5)

def test_adverse_price_drift_buy(guard):
    # Buy signal at 100, market jumped to 101.0 (1.0% drift > 0.5% allowed)
    res = guard.validate_execution_price("BUY", 100.0, 101.0, signal_timestamp=100.0, current_timestamp=101.5)
    assert res["allowed"] is False
    assert res["reason"] == "ADVERSE_PRICE_DRIFT"

def test_acceptable_and_adverse_drift_sell(guard):
    # Sell signal at 100, market at 99.7 (0.3% drop <= 0.5% allowed)
    res_ok = guard.validate_execution_price("SELL", 100.0, 99.7, signal_timestamp=100.0, current_timestamp=101.0)
    assert res_ok["allowed"] is True

    # Sell signal at 100, market crashed to 99.0 (1.0% drop > 0.5% allowed)
    res_fail = guard.validate_execution_price("SELL", 100.0, 99.0, signal_timestamp=100.0, current_timestamp=101.0)
    assert res_fail["allowed"] is False
    assert res_fail["reason"] == "ADVERSE_PRICE_DRIFT"
