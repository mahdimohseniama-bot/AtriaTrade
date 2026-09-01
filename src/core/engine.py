import time
import logging
from typing import Dict, Any
from src.market.market_fetcher import MarketFetcher
from src.strategies.sma_cross import SMACrossStrategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

class TradingEngine:
    def __init__(self, initial_balance: float = 1000.0, symbol: str = "BTC/USDT"):
        self.balance = initial_balance
        self.symbol = symbol
        self.position = 0.0  # مقدار دارایی خریداری شده
        self.entry_price = 0.0
        self.fetcher = MarketFetcher()
        self.strategy = SMACrossStrategy(short_window=3, long_window=5)
        self.trade_history = []
        logging.info(f"Engine initialized with Balance: ${self.balance:.2f} for Symbol: {self.symbol}")

    def execute_tick(self) -> Dict[str, Any]:
        """یک گام معاملاتی: دریافت قیمت، تولید سیگنال و مدیریت پوزیشن"""
        ticker = self.fetcher.get_ticker(self.symbol)
        current_price = ticker['last']
        self.strategy.add_price(current_price)
        
        signal = self.strategy.generate_signal(current_price)
        action_taken = "HOLD"

        # منطق خرید (BUY)
        if signal == "BUY" and self.position == 0.0 and self.balance > 10.0:
            self.position = (self.balance * 0.95) / current_price  # 95% سرمایه
            self.balance -= self.position * current_price
            self.entry_price = current_price
            action_taken = f"BOUGHT {self.position:.6f} {self.symbol} @ {current_price}"
            logging.info(f"🟢 [BUY] {action_taken}")

        # منطق فروش (SELL)
        elif signal == "SELL" and self.position > 0.0:
            sell_value = self.position * current_price
            pnl = sell_value - (self.position * self.entry_price)
            self.balance += sell_value
            action_taken = f"SOLD {self.position:.6f} @ {current_price} | PnL: ${pnl:+.2f}"
            logging.info(f"🔴 [SELL] {action_taken} | New Balance: ${self.balance:.2f}")
            self.position = 0.0
            self.entry_price = 0.0

        return {
            "symbol": self.symbol,
            "price": current_price,
            "signal": signal,
            "action": action_taken,
            "balance": round(self.balance, 2),
            "position": round(self.position, 6)
        }
