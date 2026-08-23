"""
ExchangeSimulator for AtriaTrade.

This module only provides simulated market data.
It does not connect to a real exchange and cannot place real orders.
"""

from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, Iterator, List, Optional


@dataclass
class Candle:
    """A single OHLCV market candle."""

    timestamp: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str = "1m"

    def to_dict(self) -> Dict[str, object]:
        """Return the candle as a dictionary."""
        return asdict(self)


class ExchangeSimulator:
    """
    Safe simulated exchange for Paper Trading and Backtesting.

    No real exchange API is used.
    No real order can be submitted through this class.
    """

    def __init__(
        self,
        initial_prices: Optional[Dict[str, float]] = None,
        seed: int = 42,
    ):
        self.prices: Dict[str, float] = {}
        self._random = random.Random(seed)
        self._running = False

        if initial_prices is None:
            initial_prices = {
                "BTCUSDT": 50000.0,
                "ETHUSDT": 3000.0,
                "XAUUSDT": 2000.0,
            }

        for symbol, price in initial_prices.items():
            self._validate_symbol(symbol)
            self._validate_price(price)
            self.prices[symbol.upper()] = float(price)

    @staticmethod
    def _validate_symbol(symbol: str) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")

    @staticmethod
    def _validate_price(price: float) -> None:
        try:
            value = float(price)
        except (TypeError, ValueError) as exc:
            raise ValueError("price must be numeric") from exc

        if value <= 0:
            raise ValueError("price must be greater than zero")

    def get_price(self, symbol: str) -> float:
        """Return the latest simulated price."""
        self._validate_symbol(symbol)
        symbol = symbol.upper()

        if symbol not in self.prices:
            raise KeyError(f"Unknown simulated symbol: {symbol}")

        return self.prices[symbol]

    def set_price(self, symbol: str, price: float) -> float:
        """Set and return a simulated market price."""
        self._validate_symbol(symbol)
        self._validate_price(price)

        symbol = symbol.upper()
        self.prices[symbol] = float(price)
        return self.prices[symbol]

    def create_candle(
        self,
        symbol: str,
        close_price: Optional[float] = None,
        timestamp: Optional[int] = None,
        interval: str = "1m",
        volume: Optional[float] = None,
    ) -> Candle:
        """Create one simulated OHLCV candle."""
        self._validate_symbol(symbol)
        symbol = symbol.upper()

        if symbol not in self.prices:
            raise KeyError(f"Unknown simulated symbol: {symbol}")

        previous_price = self.prices[symbol]

        if close_price is None:
            change = self._random.uniform(-0.01, 0.01)
            close_price = previous_price * (1.0 + change)

        self._validate_price(close_price)
        close_price = float(close_price)

        high = max(previous_price, close_price) * (
            1.0 + self._random.uniform(0.0, 0.002)
        )
        low = min(previous_price, close_price) * (
            1.0 - self._random.uniform(0.0, 0.002)
        )

        if volume is None:
            volume = self._random.uniform(1.0, 100.0)

        if float(volume) <= 0:
            raise ValueError("volume must be greater than zero")

        if timestamp is None:
            timestamp = int(time.time() * 1000)

        self.prices[symbol] = close_price

        return Candle(
            timestamp=int(timestamp),
            symbol=symbol,
            open=round(previous_price, 8),
            high=round(high, 8),
            low=round(low, 8),
            close=round(close_price, 8),
            volume=round(float(volume), 8),
            interval=interval,
        )

    def stream_candles(
        self,
        symbol: str,
        prices: Optional[Iterable[float]] = None,
        interval: str = "1m",
        delay_seconds: float = 0.0,
    ) -> Iterator[Candle]:
        """
        Stream candles from fixed prices or simulated random prices.

        If prices is provided, one candle is produced for each price.
        If prices is omitted, the stream continues until stop() is called.
        """
        self._validate_symbol(symbol)

        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")

        self._running = True

        if prices is not None:
            for price in prices:
                if not self._running:
                    break

                yield self.create_candle(
                    symbol=symbol,
                    close_price=float(price),
                    interval=interval,
                )

                if delay_seconds > 0:
                    time.sleep(delay_seconds)

            self._running = False
            return

        while self._running:
            yield self.create_candle(symbol=symbol, interval=interval)

            if delay_seconds > 0:
                time.sleep(delay_seconds)

    def run_callback(
        self,
        symbol: str,
        callback: Callable[[Candle], None],
        prices: Optional[Iterable[float]] = None,
        interval: str = "1m",
        delay_seconds: float = 0.0,
    ) -> int:
        """Send each generated candle to a callback function."""
        if not callable(callback):
            raise ValueError("callback must be callable")

        count = 0

        for candle in self.stream_candles(
            symbol=symbol,
            prices=prices,
            interval=interval,
            delay_seconds=delay_seconds,
        ):
            callback(candle)
            count += 1

        return count

    def stop(self) -> None:
        """Stop an active simulated data stream."""
        self._running = False

    def get_status(self) -> Dict[str, object]:
        """Return simulator status."""
        return {
            "mode": "SIMULATION_ONLY",
            "real_trading_enabled": False,
            "running": self._running,
            "symbols": sorted(self.prices.keys()),
            "prices": dict(self.prices),
        }
