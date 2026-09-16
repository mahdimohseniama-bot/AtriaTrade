from src.core.order_manager import OrderManager


def test_order_lifecycle():
    print("[1] Creating OrderManager...")
    manager = OrderManager()

    print("[2] Creating LIMIT BUY order...")
    order = manager.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=0.1,
        price=50000.0,
    )

    assert order["symbol"] == "BTCUSDT"
    assert order["side"] == "BUY"
    assert order["order_type"] == "LIMIT"
    assert order["quantity"] == 0.1
    assert order["price"] == 50000.0
    assert order["status"] == "OPEN"
    print("-> Order created successfully.")

    print("[3] Checking open orders...")
    open_orders = manager.list_open_orders("BTCUSDT")

    assert len(open_orders) == 1
    assert open_orders[0]["order_id"] == order["order_id"]
    assert manager.get_order_status(order["order_id"]) == "OPEN"
    print("-> Open order status validated.")

    print("[4] Testing duplicate order protection...")
    try:
        manager.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.1,
            price=50000.0,
        )
        raise AssertionError("Duplicate order was not rejected.")
    except ValueError as error:
        assert "identical" in str(error).lower()

    print("-> Duplicate order rejected successfully.")

    print("[5] Filling order...")
    filled_order = manager.fill_order(
        order["order_id"],
        fill_price=50100.0,
    )

    assert filled_order["status"] == "FILLED"
    assert filled_order["fill_price"] == 50100.0
    assert manager.list_open_orders("BTCUSDT") == []
    print("-> Order filled successfully.")

    print("[6] Creating and cancelling another order...")
    second_order = manager.create_order(
        symbol="ETHUSDT",
        side="SELL",
        order_type="LIMIT",
        quantity=1.0,
        price=3000.0,
    )

    cancelled_order = manager.cancel_order(second_order["order_id"])

    assert cancelled_order["status"] == "CANCELLED"
    assert manager.get_order_status(second_order["order_id"]) == "CANCELLED"
    print("-> Order cancelled successfully.")

    print("=== ORDER MANAGER TEST PASSED ===")


def test_order_validation():
    manager = OrderManager()

    invalid_cases = [
        {
            "symbol": "BTCUSDT",
            "side": "INVALID",
            "order_type": "MARKET",
            "quantity": 1.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 1.0,
        },
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": 0,
        },
    ]

    for case in invalid_cases:
        try:
            manager.create_order(**case)
            raise AssertionError("Invalid order was accepted.")
        except ValueError:
            pass

    print("=== ORDER VALIDATION TEST PASSED ===")


if __name__ == "__main__":
    test_order_lifecycle()
    test_order_validation()
