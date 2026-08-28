"""Unit tests for PortfolioRiskManager (Pure Python)."""

import pytest
from src.core.portfolio_risk import PortfolioRiskManager


def test_portfolio_risk_allowed_trade():
    prm = PortfolioRiskManager(
        max_total_exposure_pct=0.8,
        max_single_asset_exposure_pct=0.3,
        max_open_positions=5
    )
    positions = [
        {"symbol": "BTC/USDT", "value": 100.0}
    ]
    res = prm.validate_new_position(
        portfolio_balance=1000.0,
        current_positions=positions,
        new_symbol="ETH/USDT",
        new_position_value=200.0
    )
    assert res["allowed"] is True
    assert res["projected_total_exposure_pct"] == 0.3
    assert res["projected_symbol_exposure_pct"] == 0.2


def test_portfolio_risk_exceeds_single_asset():
    prm = PortfolioRiskManager(max_single_asset_exposure_pct=0.25)
    positions = [
        {"symbol": "BTC/USDT", "value": 200.0}
    ]
    res = prm.validate_new_position(
        portfolio_balance=1000.0,
        current_positions=positions,
        new_symbol="BTC/USDT",
        new_position_value=100.0  # 300 total = 30% > 25%
    )
    assert res["allowed"] is False
    assert "Single asset exposure" in res["reason"]


def test_portfolio_risk_exceeds_max_positions():
    prm = PortfolioRiskManager(max_open_positions=2)
    positions = [
        {"symbol": "BTC/USDT", "value": 50.0},
        {"symbol": "ETH/USDT", "value": 50.0}
    ]
    res = prm.validate_new_position(
        portfolio_balance=1000.0,
        current_positions=positions,
        new_symbol="SOL/USDT",
        new_position_value=50.0
    )
    assert res["allowed"] is False
    assert "Maximum open positions" in res["reason"]


def test_portfolio_risk_daily_drawdown_limit():
    prm = PortfolioRiskManager(max_portfolio_daily_loss_pct=0.04)
    res = prm.validate_new_position(
        portfolio_balance=1000.0,
        current_positions=[],
        new_symbol="BTC/USDT",
        new_position_value=100.0,
        daily_pnl_pct=-0.05  # -5% exceeds -4% limit
    )
    assert res["allowed"] is False
    assert "Daily portfolio loss limit reached" in res["reason"]


def test_portfolio_risk_correlation_guard():
    prm = PortfolioRiskManager(max_correlated_exposure_pct=0.40)
    positions = [
        {"symbol": "BTC/USDT", "value": 250.0}
    ]
    corr_matrix = {
        "ETH/USDT": {"BTC/USDT": 0.85},
        "BTC/USDT": {"ETH/USDT": 0.85}
    }
    # New ETH order of 200 => BTC (250) + ETH (200) = 450 (45% > 40%)
    res = prm.validate_new_position(
        portfolio_balance=1000.0,
        current_positions=positions,
        new_symbol="ETH/USDT",
        new_position_value=200.0,
        correlation_matrix=corr_matrix
    )
    assert res["allowed"] is False
    assert "Correlated exposure" in res["reason"]
