from src.exchange.wallex_micro_plan import WallexMicroPlanEngine

def test_stage19_valid_micro_plan_generation():
    print("[STAGE 19] TESTING VALID MICRO PLAN GENERATION...")
    engine = WallexMicroPlanEngine(min_notional_tmn=100_000.0, max_capital_pct=0.05)

    balance = 5_000_000.0  # 5M TMN
    price = 60_000.0       # 60k TMN per USDT

    plan = engine.generate_plan(
        symbol="TMNUSDT",
        side="BUY",
        best_price=price,
        available_balance=balance,
        risk_rr_ratio=2.0,
        sl_pct=0.02
    )

    assert plan.is_valid is True
    assert plan.rejection_reason is None
    assert plan.total_value >= 100_000.0
    assert plan.stop_loss == round(price * 0.98, 2)
    assert plan.take_profit == round(price * (1.0 + 0.04), 2)
    print("[SUCCESS] Stage 19 Valid Micro Plan Generation Passed!")

def test_stage19_reject_insufficient_balance():
    print("[STAGE 19] TESTING REJECT INSUFFICIENT BALANCE...")
    engine = WallexMicroPlanEngine(min_notional_tmn=100_000.0, max_capital_pct=0.05)

    balance = 50_000.0  # Less than min notional
    price = 60_000.0

    plan = engine.generate_plan(
        symbol="TMNUSDT",
        side="BUY",
        best_price=price,
        available_balance=balance
    )

    assert plan.is_valid is False
    assert plan.rejection_reason == "INSUFFICIENT_BALANCE_FOR_MIN_NOTIONAL"
    print("[SUCCESS] Stage 19 Insufficient Balance Rejection Passed!")

def test_stage19_sell_side_brackets():
    print("[STAGE 19] TESTING SELL SIDE BRACKETS...")
    engine = WallexMicroPlanEngine(min_notional_tmn=100_000.0, max_capital_pct=0.10)

    balance = 2_000_000.0
    price = 100.0

    plan = engine.generate_plan(
        symbol="TMNCOIN",
        side="SELL",
        best_price=price,
        available_balance=balance,
        risk_rr_ratio=1.5,
        sl_pct=0.05
    )

    assert plan.is_valid is True
    assert plan.stop_loss > price
    assert plan.take_profit < price
    print("[SUCCESS] Stage 19 Sell Side Brackets Passed!")

if __name__ == "__main__":
    test_stage19_valid_micro_plan_generation()
    test_stage19_reject_insufficient_balance()
    test_stage19_sell_side_brackets()
    print("[SUCCESS] Stage 19 Micro Plan Engine Passed!")
