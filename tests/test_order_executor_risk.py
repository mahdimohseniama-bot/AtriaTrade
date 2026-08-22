"""تست اتصال OrderExecutor به RiskManager — AtriaTrade"""
from src.core.order_executor import OrderExecutor
from src.core.order_manager import OrderManager, OrderSide, OrderType, OrderStatus
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskManager


def build_executor() -> OrderExecutor:
    risk_manager = RiskManager(
        capital=10000.0,
        max_risk_percent=1.0,
        max_position_percent=50.0,
        max_daily_loss_percent=5.0,
    )
    return OrderExecutor(
        order_manager=OrderManager(),
        position_tracker=PositionTracker(),
        risk_manager=risk_manager,
    )


def test_market_order_allowed():
    print("[1] اجرای سفارش Market مجاز...")
    ex = build_executor()
    result = ex.execute_market_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        quantity=0.1,
        price=50000.0,
        stop_loss=49000.0,
        take_profit=53000.0,
    )
    assert result["status"] == OrderStatus.FILLED.value, result
    assert result["filled_price"] == 50000.0
    assert result["filled_quantity"] == 0.1
    pos = ex.position_tracker.get_position("BTCUSDT")
    assert pos is not None
    assert pos.quantity == 0.1
    assert pos.entry_price == 50000.0
    print("-> سفارش پر شد و پوزیشن باز شد.")


def test_market_order_rejected_by_position_value():
    print("[2] رد سفارش Market به دلیل ارزش بیش‌ازحد پوزیشن...")
    ex = build_executor()
    try:
        ex.execute_market_order(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            quantity=0.2,
            price=50000.0,
            stop_loss=49000.0,
        )
    except ValueError as e:
        print(f"-> درست رد شد: {e}")
        return
    raise AssertionError("باید ValueError صادر می‌شد (ارزش پوزیشن بیش از حد)")


def test_market_order_rejected_by_wrong_stop_loss():
    print("[3] رد سفارش Market به دلیل جهت اشتباه حد ضرر...")
    ex = build_executor()
    try:
        ex.execute_market_order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            stop_loss=51000.0,
        )
    except ValueError as e:
        print(f"-> درست رد شد: {e}")
        return
    raise AssertionError("باید ValueError صادر می‌شد (حد ضرر بالاتر از ورود در BUY)")


def test_daily_loss_limit():
    print("[4] بررسی سقف ضرر روزانه...")
    ex = build_executor()
    ex.risk_manager.record_daily_loss(400.0)
    ex.risk_manager.record_daily_loss(150.0)
    assert ex.risk_manager.get_today_loss() == 550.0
    assert ex.risk_manager.can_trade_today() is False
    try:
        ex.execute_market_order(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=0.1,
            price=50000.0,
            stop_loss=49000.0,
        )
    except ValueError as e:
        print(f"-> درست مسدود شد: {e}")
    else:
        raise AssertionError("باید ValueError صادر می‌شد (سقف ضرر روزانه)")
    ex.risk_manager.reset_daily_loss()
    assert ex.risk_manager.can_trade_today() is True
    print("-> سقف ضرر روزانه و reset آن درست کار می‌کند.")


def test_limit_order_flow():
    print("[5] بررسی سفارش Limit (صبر تا رسیدن قیمت)...")
    ex = build_executor()
    order = ex.order_manager.create_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=0.1,
        price=49000.0,
        stop_loss=48000.0,
        take_profit=52000.0,
    )
    result = ex.process_limit_order(order.order_id, current_price=49500.0)
    assert result["status"] == OrderStatus.PENDING.value, result
    result = ex.process_limit_order(order.order_id, current_price=48900.0)
    assert result["status"] == OrderStatus.FILLED.value, result
    assert ex.position_tracker.get_position("BTCUSDT") is not None
    print("-> سفارش Limit بعد از رسیدن قیمت پر شد.")


def test_sell_order():
    print("[6] اجرای سفارش SELL...")
    ex = build_executor()
    result = ex.execute_market_order(
        symbol="ETHUSDT",
        side=OrderSide.SELL,
        quantity=0.1,
        price=3000.0,
        stop_loss=3100.0,
        take_profit=2800.0,
    )
    assert result["status"] == OrderStatus.FILLED.value, result
    pos = ex.position_tracker.get_position("ETHUSDT")
    assert pos is not None
    assert pos.side == OrderSide.SELL.value
    print("-> سفارش SELL پر شد و پوزیشن باز شد.")


if __name__ == "__main__":
    test_market_order_allowed()
    test_market_order_rejected_by_position_value()
    test_market_order_rejected_by_wrong_stop_loss()
    test_daily_loss_limit()
    test_limit_order_flow()
    test_sell_order()
    print("=== ORDER EXECUTOR RISK TEST PASSED ===")
