from src.core.order_executor import OrderExecutor


def test_market_execution_flow():
    print("[1] Initializing OrderExecutor...")
    executor = OrderExecutor()

    print("[2] Executing MARKET BUY order...")
    result = executor.place_and_execute_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.2,
        current_price=50000.0,
        sl=49000.0,
        tp=52000.0,
    )

    assert result["order"]["status"] == "FILLED"
    assert result["position"]["symbol"] == "BTCUSDT"
    assert result["position"]["entry_price"] == 50000.0
    assert result["position"]["size"] == 0.2
    assert executor.position_tracker.get_position("BTCUSDT") is not None
    print("-> Market order executed and position tracked successfully.")

    print("=== MARKET EXECUTION TEST PASSED ===")


def test_limit_order_trigger_flow():
    print("[3] Testing LIMIT order triggering...")
    executor = OrderExecutor()

    # ثبت سفارش لیمیت خرید پایین‌تر از قیمت بازار
    order = executor.order_manager.create_order(
        symbol="ETHUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=1.5,
        price=2900.0,
    )
    assert order["status"] == "OPEN"

    # قیمت جاری بالاتر است -> نباید Fill شود
    executions = executor.evaluate_limit_orders("ETHUSDT", current_price=3000.0)
    assert len(executions) == 0
    assert executor.order_manager.get_order_status(order["order_id"]) == "OPEN"

    # قیمت افت می‌کند و به تارگت لیمیت می‌رسد -> باید Fill شود
    executions = executor.evaluate_limit_orders("ETHUSDT", current_price=2890.0)
    assert len(executions) == 1
    assert executions[0]["order"]["status"] == "FILLED"
    assert executor.position_tracker.get_position("ETHUSDT") is not None
    print("-> Limit order evaluated and triggered successfully.")

    print("=== LIMIT EXECUTION TEST PASSED ===")


if __name__ == "__main__":
    test_market_execution_flow()
    test_limit_order_trigger_flow()
