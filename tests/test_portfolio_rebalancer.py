from src.core.portfolio_rebalancer import PortfolioRebalancer


def test_calculate_current_allocations():
    rebalancer = PortfolioRebalancer()

    balances = {"BTC": 1.0, "ETH": 10.0, "USDT": 10000.0}
    prices = {"BTC": 50000.0, "ETH": 4000.0}
    # BTC = 50k, ETH = 40k, USDT = 10k -> Total = 100k

    allocations = rebalancer.calculate_current_allocations(balances, prices)
    assert round(allocations["BTC"], 2) == 0.50
    assert round(allocations["ETH"], 2) == 0.40
    assert round(allocations["USDT"], 2) == 0.10


def test_generate_rebalance_orders():
    # Drift threshold 5%
    rebalancer = PortfolioRebalancer(drift_threshold_pct=0.05)

    balances = {"BTC": 1.0, "USDT": 50000.0}
    prices = {"BTC": 50000.0}
    # Total = 100k -> Current: BTC=50%, USDT=50%

    # Target: BTC=70% (Target USD: 70k -> Need to BUY 20k USD of BTC = 0.4 BTC)
    target_weights = {"BTC": 0.70, "USDT": 0.30}

    orders = rebalancer.generate_rebalance_orders(balances, prices, target_weights)
    assert len(orders) == 2  # Rebalance order for BTC and USDT

    btc_order = next(o for o in orders if o["asset"] == "BTC")
    assert btc_order["side"] == "BUY"
    assert round(btc_order["amount"], 4) == 0.4000
    assert round(btc_order["drift_pct"], 1) == 20.0
