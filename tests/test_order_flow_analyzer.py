import pytest
from src.core.order_flow_analyzer import OrderFlowAnalyzer


def test_static_imbalance_balanced():
    analyzer = OrderFlowAnalyzer(depth_levels=3)
    bids = [[100.0, 5.0], [99.0, 5.0], [98.0, 5.0]]
    asks = [[101.0, 5.0], [102.0, 5.0], [103.0, 5.0]]
    
    imbalance = analyzer.calculate_static_imbalance(bids, asks)
    assert imbalance == pytest.approx(0.0)


def test_static_imbalance_bullish():
    analyzer = OrderFlowAnalyzer(depth_levels=2)
    bids = [[100.0, 15.0], [99.0, 15.0]]
    asks = [[101.0, 5.0], [102.0, 5.0]]
    
    imbalance = analyzer.calculate_static_imbalance(bids, asks)
    # (30 - 10) / (30 + 10) = 20 / 40 = 0.5
    assert imbalance == pytest.approx(0.5)


def test_static_imbalance_empty():
    analyzer = OrderFlowAnalyzer()
    assert analyzer.calculate_static_imbalance([], []) == 0.0


def test_delta_ofi_tracking():
    analyzer = OrderFlowAnalyzer()
    t0_bids = [[100.0, 10.0]]
    t0_asks = [[101.0, 10.0]]
    
    # بار اول فقط ذخیره می‌شود
    assert analyzer.calculate_delta_ofi(t0_bids, t0_asks) == 0.0

    # افزایش قیمت Bid (فشار خرید شدید)
    t1_bids = [[100.5, 12.0]]
    t1_asks = [[101.0, 10.0]]
    ofi = analyzer.calculate_delta_ofi(t1_bids, t1_asks)
    assert ofi > 0


def test_analyze_market_pressure_signals():
    analyzer = OrderFlowAnalyzer(imbalance_threshold=0.25)
    bids = [[100.0, 20.0], [99.0, 20.0]]
    asks = [[101.0, 5.0], [102.0, 5.0]]
    
    res = analyzer.analyze_market_pressure(bids, asks)
    assert res["is_valid"] is True
    assert res["sentiment"] == "BULLISH_PRESSURE"
    assert res["imbalance_ratio"] == pytest.approx(0.6)
