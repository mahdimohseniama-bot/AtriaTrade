import pytest
from src.core.portfolio_drawdown_circuit_breaker import PortfolioDrawdownCircuitBreaker


def test_circuit_breaker_normal_state():
    cb = PortfolioDrawdownCircuitBreaker(
        max_total_drawdown_pct=10.0,
        max_daily_drawdown_pct=4.0,
        warning_drawdown_pct=5.0
    )
    res = cb.update_equity(10000.0)
    assert res["is_tripped"] is False
    assert res["risk_multiplier"] == 1.0
    assert cb.can_open_new_trade() is True


def test_circuit_breaker_warning_soft_threshold():
    # سقف روزانه روی ۱۰٪ و هشدار روی ۵٪
    cb = PortfolioDrawdownCircuitBreaker(
        max_total_drawdown_pct=15.0,
        max_daily_drawdown_pct=10.0,
        warning_drawdown_pct=5.0
    )
    cb.update_equity(10000.0)  # قله روی ۱۰۰۰۰
    res = cb.update_equity(9400.0)  # افت ۶٪ (بین ۵٪ و ۱۰٪)
    assert res["is_tripped"] is False
    assert res["risk_multiplier"] == 0.5
    assert cb.can_open_new_trade() is True


def test_circuit_breaker_hard_total_drawdown_trip():
    cb = PortfolioDrawdownCircuitBreaker(
        max_total_drawdown_pct=10.0,
        max_daily_drawdown_pct=8.0,
        warning_drawdown_pct=5.0
    )
    cb.update_equity(10000.0)  # قله
    res = cb.update_equity(8900.0)  # افت ۱۱٪
    assert res["is_tripped"] is True
    assert res["risk_multiplier"] == 0.0
    assert cb.can_open_new_trade() is False
    assert "MAX_TOTAL_DRAWDOWN_EXCEEDED" in res["trip_reason"]


def test_circuit_breaker_reset():
    cb = PortfolioDrawdownCircuitBreaker(max_total_drawdown_pct=10.0)
    cb.update_equity(10000.0)
    cb.update_equity(8500.0)
    assert cb.is_tripped is True

    cb.reset_circuit_breaker(reset_peak=True, current_equity=8500.0)
    assert cb.is_tripped is False
    assert cb.can_open_new_trade() is True
    assert cb.peak_equity == 8500.0
