from src.core.order_simulator import OrderSimulator


def test_market_buy_order() -> None:
    simulator = OrderSimulator(
        fee_percent=0.1,
        slippage_percent=0.05,
    )

    order = simulator.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.01,
        price=100000.0,
    )

    assert order["status"] == "FILLED"
    assert order["executed_price"] > 100000.0
    assert order["fee"] > 0

    print("[OK] Market BUY simulation passed")


def test_market_sell_order() -> None:
    simulator = OrderSimulator(
        fee_percent=0.1,
        slippage_percent=0.05,
    )

    order = simulator.create_order(
        symbol="BTCUSDT",
        side="SELL",
        order_type="MARKET",
        quantity=0.01,
        price=100000.0,
    )

    assert order["status"] == "FILLED"
    assert order["executed_price"] < 100000.0
    assert order["fee"] > 0

    print("[OK] Market SELL simulation passed")


def test_limit_order_states() -> None:
    simulator = OrderSimulator(
        fee_percent=0.1,
        slippage_percent=0.0,
    )

    unfilled_order = simulator.create_order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1.0,
        price=2000.0,
        limit_price=1900.0,
    )

    assert unfilled_order["status"] == "NEW"
    assert len(simulator.get_active_orders()) == 1

    canceled_order = simulator.cancel_order(
        unfilled_order["order_id"]
    )

    assert canceled_order["status"] == "CANCELED"
    assert len(simulator.get_active_orders()) == 0

    filled_order = simulator.create_order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1.0,
        price=1900.0,
        limit_price=2000.0,
    )

    assert filled_order["status"] == "FILLED"
    assert len(simulator.get_filled_orders()) == 1
    assert len(simulator.get_all_orders()) == 2

    print("[OK] LIMIT order state management passed")


def test_invalid_order_rejection() -> None:
    simulator = OrderSimulator()

    invalid_cases = [
        {
            "symbol": "BTCUSDT",
            "side": "HOLD",
            "order_type": "MARKET",
            "quantity": 1.0,
            "price": 100.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0.0,
            "price": 100.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 1.0,
            "price": 0.0,
        },
    ]

    for case in invalid_cases:
        try:
            simulator.create_order(**case)
        except ValueError:
            continue

        raise AssertionError("Invalid order was accepted")

    print("[OK] Invalid order rejection passed")


def run_tests() -> None:
    test_market_buy_order()
    test_market_sell_order()
    test_limit_order_states()
    test_invalid_order_rejection()

    print("=== ORDER SIMULATOR TEST PASSED ===")


if __name__ == "__main__":
    run_tests()
