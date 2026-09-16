"""
AtriaTrade - Data Feed Manager

هماهنگ‌کننده دریافت، اعتبارسنجی و نگهداری داده‌های OHLCV.
این ماژول فقط برای Paper Trading / Backtesting طراحی شده است.
"""

from typing import Any, Dict, List, Optional

from src.data.market_fetcher import MarketFetcher
from src.data.candle_validator import CandleValidator


Candle = Dict[str, Any]


class DataFeedManager:
    """
    دریافت داده از MarketFetcher، اعتبارسنجی با CandleValidator
    و نگهداری کندل‌های معتبر در بافر داخلی.
    """

    def __init__(
        self,
        fetcher: MarketFetcher,
        validator: CandleValidator,
        exchange_name: str,
        max_buffer_size: int = 1000,
    ) -> None:
        """
        Args:
            fetcher: نمونه MarketFetcher.
            validator: نمونه CandleValidator.
            exchange_name: نام صرافی، مانند binance / nobitex / wallex.
            max_buffer_size: حداکثر تعداد کندل ذخیره‌شده برای هر نماد و تایم‌فریم.
        """
        if not isinstance(exchange_name, str) or not exchange_name.strip():
            raise ValueError("exchange_name نباید خالی باشد.")

        if not isinstance(max_buffer_size, int) or max_buffer_size <= 0:
            raise ValueError("max_buffer_size باید یک عدد صحیح بزرگ‌تر از صفر باشد.")

        self.fetcher = fetcher
        self.validator = validator
        self.exchange_name = exchange_name.strip().lower()
        self.max_buffer_size = max_buffer_size

        # ساختار:
        # _data[exchange_name][symbol][timeframe] = [candle, ...]
        self._data: Dict[str, Dict[str, Dict[str, List[Candle]]]] = {}

    def update_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> List[Candle]:
        """
        دریافت کندل، اعتبارسنجی آن و ذخیره در بافر.

        Returns:
            لیست کندل‌های معتبر ذخیره‌شده در بافر.
        """
        raw_candles = self.fetcher.fetch_ohlcv(
            exchange_name=self.exchange_name,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        validated_candles = self.validator.validate(
            candles=raw_candles,
            timeframe=timeframe,
            require_continuity=False,
        )

        exchange_data = self._data.setdefault(self.exchange_name, {})
        symbol_data = exchange_data.setdefault(symbol, {})

        # در این مرحله داده جدید جایگزین snapshot قبلی می‌شود.
        symbol_data[timeframe] = validated_candles[-self.max_buffer_size :]

        return self.get_candles(symbol, timeframe)

    def get_candles(self, symbol: str, timeframe: str) -> List[Candle]:
        """
        دریافت کپی از کندل‌های ذخیره‌شده برای نماد و تایم‌فریم موردنظر.
        """
        candles = (
            self._data
            .get(self.exchange_name, {})
            .get(symbol, {})
            .get(timeframe, [])
        )

        # کپی سطحی: کد بیرونی نتواند مستقیماً لیست بافر را تغییر دهد.
        return list(candles)

    def get_latest_candle(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[Candle]:
        """
        دریافت جدیدترین کندل ذخیره‌شده.
        """
        candles = self.get_candles(symbol, timeframe)
        return candles[-1] if candles else None
