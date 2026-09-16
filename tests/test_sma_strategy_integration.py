from src.strategies.sma_cross_strategy import SMACrossStrategy


class FakeTradingEngine:
    """
    موتور کاملاً آزمایشی برای تست Paper Trading.
    هیچ اتصال واقعی یا سفارش واقعی ندارد.
    """

    def __init__(self):
        self.portfolio = {}
        self.received_signals = []
        self.paper_orders = []

    def handle_strategy_signal(self, strategy_name, signal):
        self.received_signals.append(
            {
                "strategy_name": strategy_name,
                "signal": signal,
            }
        )

        order = {
            "symbol": signal["symbol"],
            "side": signal["side"],
            "qty": signal.get("qty", signal.get("quantity")),
            "price": signal["price"],
            "status": "FILLED",
            "mode": "PAPER",
        }

        self.paper_orders.append(order)

        symbol = order["symbol"]
        quantity = float(order["qty"])

        if order["side"] == "BUY":
            self.portfolio[symbol] = quantity

        elif order["side"] == "SELL":
            self.portfolio[symbol] = 0.0

        return order


def test_strategy_dispatches_buy_signal_to_engine():
    engine = FakeTradingEngine()

    strategy = SMACrossStrategy(
        engine=engine,
        short_window=3,
        long_window=6,
        symbol="BTCUSDT",
        quantity=1.0,
    )

    prices = [100, 101, 102, 103, 105, 110, 120]

    for price in prices:
        strategy.on_tick(
            {
                "symbol": "BTCUSDT",
                "price": price,
            }
        )

    assert len(engine.received_signals) >= 1

    first_signal = engine.received_signals[0]

    assert first_signal["strategy_name"] == "SMACrossStrategy"
    assert first_signal["signal"]["symbol"] == "BTCUSDT"
    assert first_signal["signal"]["side"] == "BUY"

    assert len(engine.paper_orders) >= 1
    assert engine.paper_orders[0]["status"] == "FILLED"
    assert engine.paper_orders[0]["mode"] == "PAPER"
    assert engine.portfolio["BTCUSDT"] == 1.0


def test_strategy_dispatches_sell_signal_to_engine():
    engine = FakeTradingEngine()

    strategy = SMACrossStrategy(
        engine=engine,
        short_window=3,
        long_window=6,
        symbol="BTCUSDT",
        quantity=1.0,
    )

    rising_prices = [100, 101, 102, 103, 105, 110, 120]

    for price in rising_prices:
        strategy.on_tick(
            {
                "symbol": "BTCUSDT",
                "price": price,
            }
        )

    assert engine.portfolio["BTCUSDT"] == 1.0

    previous_orders = len(engine.paper_orders)

    falling_prices = [115, 110, 100, 90, 80]

    for price in falling_prices:
        strategy.on_tick(
            {
                "symbol": "BTCUSDT",
                "price": price,
            }
        )

    assert len(engine.paper_orders) > previous_orders

    last_order = engine.paper_orders[-1]

    assert last_order["side"] == "SELL"
    assert last_order["status"] == "FILLED"
    assert last_order["mode"] == "PAPER"
    assert engine.portfolio["BTCUSDT"] == 0.0


def test_hold_does_not_create_paper_order():
    engine = FakeTradingEngine()

    strategy = SMACrossStrategy(
        engine=engine,
        short_window=3,
        long_window=6,
        symbol="BTCUSDT",
        quantity=1.0,
    )

    result = strategy.on_tick(
        {
            "symbol": "BTCUSDT",
            "price": 100,
        }
    )

    assert result is None
    assert engine.received_signals == []
    assert engine.paper_orders == []


def test_invalid_ticks_are_ignored():
    engine = FakeTradingEngine()

    strategy = SMACrossStrategy(
        engine=engine,
        short_window=3,
        long_window=6,
        symbol="BTCUSDT",
        quantity=1.0,
    )

    assert strategy.on_tick({}) is None
    assert strategy.on_tick({"price": "invalid"}) is None
    assert strategy.on_tick({"price": -10}) is None

    assert engine.received_signals == []
    assert engine.paper_orders == []
