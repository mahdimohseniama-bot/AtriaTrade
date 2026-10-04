from src.exchange.wallex_order_executor import WallexOrderExecutor

def test_stage15():
    print("[STAGE 15] WALLEX ORDER EXECUTOR TEST STARTING...")

    executor = WallexOrderExecutor(api_key="MOCK_KEY", dry_run=True)

    # 1. Test Below Minimum Value (100k Tomans)
    res_min = executor.place_limit_order("TMNUSDT", "BUY", price=100000.0, quantity=0.5)
    assert res_min["success"] is False
    assert res_min["reason"] == "ORDER_BELOW_MIN_VALUE"

    # 2. Test Above Safety Max Value (20M Tomans)
    res_max = executor.place_limit_order("TMNUSDT", "BUY", price=100000.0, quantity=300.0)
    assert res_max["success"] is False
    assert res_max["reason"] == "ORDER_EXCEEDS_SAFETY_LIMIT"

    # 3. Test Invalid Price / Side
    res_inv = executor.place_limit_order("TMNUSDT", "INVALID_SIDE", price=100000.0, quantity=5.0)
    assert res_inv["success"] is False
    assert res_inv["reason"] == "INVALID_SIDE"

    # 4. Test Valid Dry-Run Execution (500k Tomans order)
    res_ok = executor.place_limit_order("TMNUSDT", "BUY", price=100000.0, quantity=5.0)
    assert res_ok["success"] is True
    assert res_ok["status"] == "SIMULATED_FILLED"
    assert res_ok["mode"] == "DRY_RUN"

    print("[SUCCESS] Stage 15 Wallex Order Executor Passed!")

if __name__ == "__main__":
    test_stage15()
