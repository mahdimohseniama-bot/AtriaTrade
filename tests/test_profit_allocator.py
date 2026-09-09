"""Unit tests for ProfitAllocator (Reinvest + Cash Vault model)."""
import pytest

from src.core.profit_allocator import ProfitAllocator, ProfitSplitConfig


class FakePortfolio:
    """Minimal stand-in: trading cash plus a withdrawable vault."""

    def __init__(self, cash=1000.0):
        self.cash = cash
        self.vault_balance = 0.0


def test_config_validation():
    with pytest.raises(ValueError):
        ProfitSplitConfig(reinvest_ratio=-5).validate()
    with pytest.raises(ValueError):
        ProfitSplitConfig(min_profit_to_split=-1).validate()


def test_default_split_70_30():
    alloc = ProfitAllocator(reinvest_ratio=70.0)
    result = alloc.split(100.0)
    assert result["skipped"] is False
    assert result["reinvest_amount"] == pytest.approx(70.0)
    assert result["vault_amount"] == pytest.approx(30.0)
    assert result["reinvest_amount"] + result["vault_amount"] == pytest.approx(100.0)


def test_no_loss_on_odd_amounts():
    alloc = ProfitAllocator(reinvest_ratio=33.0)
    result = alloc.split(10.0)
    assert result["skipped"] is False
    assert result["reinvest_amount"] + result["vault_amount"] == pytest.approx(10.0)


def test_negative_profit_untouched():
    portfolio = FakePortfolio(cash=500.0)
    alloc = ProfitAllocator(portfolio=portfolio)
    result = alloc.process_trade_profit(-20.0)
    assert result["skipped"] is True
    assert portfolio.cash == pytest.approx(500.0)
    assert portfolio.vault_balance == pytest.approx(0.0)


def test_process_applies_reinvest_and_vault():
    portfolio = FakePortfolio(cash=1000.0)
    alloc = ProfitAllocator(portfolio=portfolio, reinvest_ratio=70.0)
    result = alloc.process_trade_profit(100.0)
    assert result["skipped"] is False
    assert result["action"] == "split"
    assert portfolio.cash == pytest.approx(1070.0)
    assert portfolio.vault_balance == pytest.approx(30.0)
    summary = alloc.get_summary()
    assert summary["total_profit"] == pytest.approx(100.0)
    assert summary["total_reinvested"] == pytest.approx(70.0)
    assert summary["total_vaulted"] == pytest.approx(30.0)


def test_compound_growth_over_cycles():
    portfolio = FakePortfolio(cash=1000.0)
    alloc = ProfitAllocator(portfolio=portfolio, reinvest_ratio=70.0)
    profits = (50.0, 75.0, 120.0)
    for profit in profits:
        alloc.process_trade_profit(profit)
    total = sum(profits)
    assert portfolio.cash == pytest.approx(1000.0 + total * 0.7)
    assert portfolio.vault_balance == pytest.approx(total * 0.3)
    assert alloc.split_count == 3


def test_min_profit_threshold():
    alloc = ProfitAllocator(min_profit_to_split=5.0)
    small = alloc.process_trade_profit(2.0)
    assert small["skipped"] is True
    big = alloc.process_trade_profit(10.0)
    assert big["skipped"] is False
