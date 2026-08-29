import pytest
from src.core.multi_asset_risk_allocator import MultiAssetRiskAllocator


def test_standard_allocation_approval():
    allocator = MultiAssetRiskAllocator(max_total_portfolio_risk_pct=5.0, max_single_asset_risk_pct=2.0)
    current_risks = {"BTCUSDT": 1.0, "ETHUSDT": 1.0}
    res = allocator.evaluate_allocation(current_risks, "PAXGUSDT", 1.5, "GOLD")
    assert res["approved"] is True
    assert res["allocated_risk_pct"] == 1.5
    assert res["new_total_risk_pct"] == 3.5


def test_single_asset_risk_capping():
    allocator = MultiAssetRiskAllocator(max_total_portfolio_risk_pct=5.0, max_single_asset_risk_pct=2.0)
    current_risks = {"BTCUSDT": 1.5}
    # تلاش برای اضافه کردن 1.0% دیگر روی بیت‌کوین (سقف 2.0% است پس فقط 0.5% باید تایید شود)
    res = allocator.evaluate_allocation(current_risks, "BTCUSDT", 1.0)
    assert res["approved"] is True
    assert res["allocated_risk_pct"] == 0.5
    assert res["new_total_risk_pct"] == 2.0


def test_total_portfolio_risk_exhaustion():
    allocator = MultiAssetRiskAllocator(max_total_portfolio_risk_pct=4.0, max_single_asset_risk_pct=2.0)
    current_risks = {"BTCUSDT": 2.0, "PAXGUSDT": 2.0}
    # ریسک کل پر است (4.0%)
    res = allocator.evaluate_allocation(current_risks, "ETHUSDT", 1.0)
    assert res["approved"] is False
    assert res["allocated_risk_pct"] == 0.0
