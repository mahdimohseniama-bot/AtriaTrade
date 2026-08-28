from src.core.liquidity_analyzer import OrderbookDepthAnalyzer


def test_calculate_imbalance():
    analyzer = OrderbookDepthAnalyzer(depth_limit=3)
    
    bids = [(100.0, 2.0), (99.0, 3.0), (98.0, 5.0)]  # Total 10.0
    asks = [(101.0, 1.0), (102.0, 1.0), (103.0, 2.0)] # Total 4.0

    # (10 - 4) / 14 = 6 / 14 ≈ 0.42857
    imbalance = analyzer.calculate_imbalance(bids, asks)
    assert round(imbalance, 3) == 0.429


def test_effective_vwap_and_slippage():
    analyzer = OrderbookDepthAnalyzer()

    # Asks: 1.0 @ $100, 2.0 @ $102, 5.0 @ $105
    asks = [(100.0, 1.0), (102.0, 2.0), (105.0, 5.0)]

    # Buy 2.0 units: 1.0 @ 100 + 1.0 @ 102 = 202 -> VWAP = 101.0
    vwap = analyzer.calculate_effective_vwap(asks, target_qty=2.0)
    assert vwap == 101.0

    # Best ask is 100. Slippage = (101 - 100) / 100 = 1.0%
    slippage = analyzer.estimate_market_impact_slippage(asks, order_qty=2.0, best_ask=100.0)
    assert round(slippage, 2) == 1.0

    # Insufficient liquidity test (requesting 10 units when only 8 exist)
    assert analyzer.calculate_effective_vwap(asks, target_qty=10.0) is None


def test_detect_liquidity_walls():
    analyzer = OrderbookDepthAnalyzer()

    bids = [
        (100.0, 1.0),
        (99.0, 1.2),
        (98.0, 10.0),  # Massive wall (avg is ~2.7)
        (97.0, 1.0),
        (96.0, 0.5),
    ]

    walls = analyzer.detect_liquidity_walls(bids, threshold_multiplier=3.0)
    assert len(walls) == 1
    assert walls[0]["price"] == 98.0
    assert walls[0]["volume"] == 10.0
