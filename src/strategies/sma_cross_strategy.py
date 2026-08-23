"""
SMA Cross Strategy for AtriaTrade
"""

from typing import List, Tuple, Dict, Any


class SMACrossStrategy:
    """
    Generate signals based on Short SMA and Long SMA crossover:
    - BUY: short_sma > long_sma
    - SELL: short_sma < long_sma
    - HOLD: insufficient data or equal SMAs
    """

    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 20,
        take_profit_pct: float = 0.05,
        stop_loss_pct: float = 0.02,
    ):
        if short_window <= 0:
            raise ValueError("short_window must be greater than 0")

        if long_window <= 0:
            raise ValueError("long_window must be greater than 0")

        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")

        if take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be greater than 0")

        if stop_loss_pct <= 0:
            raise ValueError("stop_loss_pct must be greater than 0")

        self.short_window = int(short_window)
        self.long_window = int(long_window)
        self.take_profit_pct = float(take_profit_pct)
        self.stop_loss_pct = float(stop_loss_pct)

    @staticmethod
    def _validate_prices(prices: List[float]) -> List[float]:
        if prices is None:
            return []

        validated = []
        for price in prices:
            value = float(price)
            if value <= 0:
                raise ValueError("Price values must be positive")
            validated.append(value)

        return validated

    @staticmethod
    def _sma(prices: List[float], window: int) -> float:
        return sum(prices[-window:]) / window

    def calculate_smas(self, prices: List[float]) -> Tuple[float, float]:
        """Calculate short and long SMAs"""
        prices = self._validate_prices(prices)

        if len(prices) < self.long_window:
            raise ValueError("Not enough data to calculate SMAs")

        short_sma = self._sma(prices, self.short_window)
        long_sma = self._sma(prices, self.long_window)

        return round(short_sma, 8), round(long_sma, 8)

    def generate_signal(self, prices: List[float]) -> str:
        """Generate BUY, SELL, or HOLD signal"""
        prices = self._validate_prices(prices)

        if len(prices) < self.long_window:
            return "HOLD"

        short_sma, long_sma = self.calculate_smas(prices)

        if short_sma > long_sma:
            return "BUY"

        if short_sma < long_sma:
            return "SELL"

        return "HOLD"

    def get_tp_sl(self, signal: str, price: float) -> Tuple[float, float]:
        """
        Calculate Take Profit and Stop Loss based on signal and price.
        Returns: (take_profit, stop_loss)
        """
        if signal not in ("BUY", "SELL"):
            return 0.0, 0.0

        price = float(price)

        if price <= 0:
            raise ValueError("Price must be greater than 0")

        if signal == "BUY":
            take_profit = price * (1 + self.take_profit_pct)
            stop_loss = price * (1 - self.stop_loss_pct)
        else:
            take_profit = price * (1 - self.take_profit_pct)
            stop_loss = price * (1 + self.stop_loss_pct)

        return round(take_profit, 8), round(stop_loss, 8)

    def get_status(self) -> Dict[str, Any]:
        """Return strategy configuration"""
        return {
            "name": "SMA Cross Strategy",
            "short_window": self.short_window,
            "long_window": self.long_window,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
        }
