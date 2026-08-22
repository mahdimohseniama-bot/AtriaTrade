from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.capital_manager import CapitalManager
from src.core.trade_history import TradeHistory
from src.exchange_simulator import ExchangeSimulator
from src.strategies.sma_cross import SMACrossStrategy


@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float
    entry_fee: float


class TraderEngine:
    def __init__(self):
        self.exchange = ExchangeSimulator()
        self.capital_manager = CapitalManager(initial_capital=100.0)
        self.strategy = SMACrossStrategy(short_window=3, long_window=5)
        self.trade_history = TradeHistory("data/trade_history.json")

        self.position: Optional[Position] = None
        self.symbol = "BTC/USDT"
        self.trade_amount = 0.001

        # قیمت‌های نمونه برای Paper Trading / Backtest
        self.price_feed = [
            100.0, 101.0, 102.0, 103.0, 105.0,
            104.0, 102.0, 100.0, 98.0
        ]

    def _buy(self, price: float):
        order = self.exchange.execute_order(
            symbol=self.symbol,
            side="buy",
            amount=self.trade_amount,
            price=price,
        )

        self.position = Position(
            symbol=self.symbol,
            amount=self.trade_amount,
            entry_price=order["price"],
            entry_fee=order["fee"],
        )

        self.trade_history.add_trade(
            symbol=self.symbol,
            side="BUY",
            amount=self.trade_amount,
            execution_price=order["price"],
            fee=order["fee"],
            net_pnl=None,
            capital_status=self.capital_manager.get_status(),
        )

        print(f"[BUY] {self.trade_amount} {self.symbol} at {order['price']:.8f} | fee={order['fee']:.8f}")

    def _sell(self, price: float):
        if self.position is None:
            return

        order = self.exchange.execute_order(
            symbol=self.symbol,
            side="sell",
            amount=self.position.amount,
            price=price,
        )

        buy_cost = self.position.amount * self.position.entry_price
        sell_value = self.position.amount * order["price"]
        total_fees = self.position.entry_fee + order["fee"]
        net_pnl = sell_value - buy_cost - total_fees

        self.capital_manager.record_trade_result(net_pnl)

        self.trade_history.add_trade(
            symbol=self.symbol,
            side="SELL",
            amount=self.position.amount,
            execution_price=order["price"],
            fee=order["fee"],
            net_pnl=net_pnl,
            capital_status=self.capital_manager.get_status(),
        )

        print(
            f"[SELL] {self.position.amount} {self.symbol} at {order['price']:.8f} | "
            f"fee={order['fee']:.8f} | net_pnl={net_pnl:.8f}"
        )

        self.position = None

    def run(self):
        print("Starting TraderEngine in PAPER TRADING mode...")
        print("-" * 60)

        for price in self.price_feed:
            signal = self.strategy.generate_signal(price)
            print(f"Price: {price:.2f} | Signal: {signal}")

            if self.position is None and signal == "BUY":
                self._buy(price)

            elif self.position is not None and signal == "SELL":
                self._sell(price)

        print("-" * 60)
        print("Final Capital Status:")
        print(self.capital_manager.get_status())
        print(f"Trade History Count: {self.trade_history.count()}")


if __name__ == "__main__":
    engine = TraderEngine()
    engine.run()
