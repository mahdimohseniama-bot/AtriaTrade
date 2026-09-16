"""
AtriaTrade - Candle Validation Module

اعتبارسنجی و استانداردسازی داده‌های OHLCV پیش از استفاده در
استراتژی، بک‌تست، تحلیل تکنیکال یا Paper Trading.

این ماژول هیچ ارتباطی با API، صرافی یا ترید واقعی ندارد.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any


class CandleValidationError(ValueError):
    """خطای مربوط به نامعتبر بودن ساختار یا محتوای دادهٔ کندل."""


class CandleValidator:
    """
    اعتبارسنج داده‌های OHLCV.

    فرمت خروجی استاندارد هر کندل:

    {
        "timestamp": 1720000000000,
        "open": 100.0,
        "high": 110.0,
        "low": 95.0,
        "close": 105.0,
        "volume": 12.5,
    }
    """

    TIMEFRAME_TO_MS = {
        "1m": 60_000,
        "3m": 3 * 60_000,
        "5m": 5 * 60_000,
        "15m": 15 * 60_000,
        "30m": 30 * 60_000,
        "1h": 60 * 60_000,
        "2h": 2 * 60 * 60_000,
        "4h": 4 * 60 * 60_000,
        "6h": 6 * 60 * 60_000,
        "12h": 12 * 60 * 60_000,
        "1d": 24 * 60 * 60_000,
        "1w": 7 * 24 * 60 * 60_000,
    }

    REQUIRED_FIELDS = (
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    def __init__(self, max_candles: int = 5_000) -> None:
        """
        Args:
            max_candles: حداکثر تعداد کندل قابل‌پردازش در هر درخواست.

        Raises:
            ValueError: اگر max_candles معتبر نباشد.
        """
        if (
            isinstance(max_candles, bool)
            or not isinstance(max_candles, int)
            or max_candles <= 0
        ):
            raise ValueError("max_candles باید یک عدد صحیح بزرگ‌تر از صفر باشد.")

        self.max_candles = max_candles

    def validate(
        self,
        candles: Iterable[Any],
        timeframe: str | None = None,
        require_continuity: bool = False,
    ) -> list[dict[str, float | int]]:
        """
        اعتبارسنجی و استانداردسازی مجموعه‌ای از کندل‌های OHLCV.

        ورودی هر کندل می‌تواند یکی از حالت‌های زیر باشد:

        1) دیکشنری:
           {
             "timestamp": ...,
             "open": ...,
             "high": ...,
             "low": ...,
             "close": ...,
             "volume": ...
           }

        2) لیست یا tuple:
           [timestamp, open, high, low, close, volume]

        Args:
            candles: مجموعهٔ کندل‌ها.
            timeframe: نمونه: 1m، 5m، 1h، 4h یا 1d.
            require_continuity: اگر True باشد فاصلهٔ زمانی تمام کندل‌ها
                باید دقیقاً برابر timeframe باشد.

        Returns:
            لیست استاندارد و اعتبارسنجی‌شدهٔ کندل‌ها.

        Raises:
            CandleValidationError: در صورت نامعتبر بودن داده‌ها.
        """
        candle_list = self._materialize_candles(candles)
        interval_ms = self._resolve_timeframe(timeframe)

        normalized_candles: list[dict[str, float | int]] = []
        previous_timestamp: int | None = None

        for index, candle in enumerate(candle_list):
            normalized = self._normalize_candle(candle, index)
            timestamp = int(normalized["timestamp"])

            if previous_timestamp is not None:
                self._validate_timestamp_order(
                    previous_timestamp=previous_timestamp,
                    current_timestamp=timestamp,
                    index=index,
                )

                if require_continuity and interval_ms is not None:
                    self._validate_continuity(
                        previous_timestamp=previous_timestamp,
                        current_timestamp=timestamp,
                        interval_ms=interval_ms,
                        index=index,
                    )

            normalized_candles.append(normalized)
            previous_timestamp = timestamp

        return normalized_candles

    def _materialize_candles(self, candles: Iterable[Any]) -> list[Any]:
        """تبدیل ورودی iterable به لیست و کنترل حجم آن."""
        if candles is None:
            raise CandleValidationError("دادهٔ کندل نمی‌تواند None باشد.")

        if isinstance(candles, (str, bytes, Mapping)):
            raise CandleValidationError(
                "candles باید یک مجموعه از کندل‌ها باشد، نه رشته یا یک کندل تکی."
            )

        try:
            candle_list = list(candles)
        except TypeError as error:
            raise CandleValidationError(
                "candles باید یک iterable معتبر باشد."
            ) from error

        if not candle_list:
            raise CandleValidationError("مجموعهٔ کندل‌ها نمی‌تواند خالی باشد.")

        if len(candle_list) > self.max_candles:
            raise CandleValidationError(
                f"تعداد کندل‌ها از حد مجاز {self.max_candles} بیشتر است."
            )

        return candle_list

    def _normalize_candle(
        self,
        candle: Any,
        index: int,
    ) -> dict[str, float | int]:
        """تبدیل یک کندل به فرمت استاندارد و اعتبارسنجی آن."""
        raw_candle = self._extract_candle_fields(candle, index)

        timestamp = self._normalize_timestamp(
            raw_candle["timestamp"],
            field_name="timestamp",
            index=index,
        )

        open_price = self._normalize_price(
            raw_candle["open"],
            field_name="open",
            index=index,
        )
        high_price = self._normalize_price(
            raw_candle["high"],
            field_name="high",
            index=index,
        )
        low_price = self._normalize_price(
            raw_candle["low"],
            field_name="low",
            index=index,
        )
        close_price = self._normalize_price(
            raw_candle["close"],
            field_name="close",
            index=index,
        )
        volume = self._normalize_volume(
            raw_candle["volume"],
            field_name="volume",
            index=index,
        )

        self._validate_price_relationships(
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            index=index,
        )

        return {
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        }

    def _extract_candle_fields(
        self,
        candle: Any,
        index: int,
    ) -> dict[str, Any]:
        """خواندن فیلدهای کندل از dict یا sequence شش‌تایی."""
        if isinstance(candle, Mapping):
            missing_fields = [
                field for field in self.REQUIRED_FIELDS if field not in candle
            ]

            if missing_fields:
                missing_text = ", ".join(missing_fields)
                raise CandleValidationError(
                    f"کندل شماره {index} فاقد فیلدهای لازم است: {missing_text}"
                )

            return {
                field: candle[field]
                for field in self.REQUIRED_FIELDS
            }

        if isinstance(candle, (list, tuple)):
            if len(candle) != 6:
                raise CandleValidationError(
                    f"کندل شماره {index} باید دقیقاً ۶ مقدار OHLCV داشته باشد."
                )

            return dict(zip(self.REQUIRED_FIELDS, candle))

        raise CandleValidationError(
            f"نوع کندل شماره {index} نامعتبر است؛ فقط dict، list یا tuple مجاز است."
        )

    def _normalize_timestamp(
        self,
        value: Any,
        field_name: str,
        index: int,
    ) -> int:
        """کنترل timestamp و تبدیل timestamp ثانیه‌ای به میلی‌ثانیه."""
        numeric_value = self._to_finite_float(value, field_name, index)

        if numeric_value <= 0:
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} باید بزرگ‌تر از صفر باشد."
            )

        timestamp = int(numeric_value)

        # timestampهای متعارف ثانیه‌ای حدود 10 رقم هستند.
        # timestamp میلی‌ثانیه‌ای حدود 13 رقم است.
        if timestamp < 10_000_000_000:
            timestamp *= 1_000

        return timestamp

    def _normalize_price(
        self,
        value: Any,
        field_name: str,
        index: int,
    ) -> float:
        """کنترل قیمت؛ قیمت باید مثبت و متناهی باشد."""
        numeric_value = self._to_finite_float(value, field_name, index)

        if numeric_value <= 0:
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} باید بزرگ‌تر از صفر باشد."
            )

        return numeric_value

    def _normalize_volume(
        self,
        value: Any,
        field_name: str,
        index: int,
    ) -> float:
        """کنترل حجم؛ حجم صفر مجاز است اما منفی مجاز نیست."""
        numeric_value = self._to_finite_float(value, field_name, index)

        if numeric_value < 0:
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} نمی‌تواند منفی باشد."
            )

        return numeric_value

    @staticmethod
    def _to_finite_float(
        value: Any,
        field_name: str,
        index: int,
    ) -> float:
        """تبدیل امن مقدار به float و جلوگیری از NaN و infinity."""
        if isinstance(value, bool):
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} نمی‌تواند bool باشد."
            )

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as error:
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} باید عددی باشد."
            ) from error

        if not math.isfinite(numeric_value):
            raise CandleValidationError(
                f"{field_name} در کندل شماره {index} باید عدد متناهی باشد."
            )

        return numeric_value

    @staticmethod
    def _validate_price_relationships(
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        index: int,
    ) -> None:
        """کنترل منطق داخلی قیمت‌های OHLC."""
        if high_price < max(open_price, close_price, low_price):
            raise CandleValidationError(
                f"high در کندل شماره {index} با قیمت‌های OHLC سازگار نیست."
            )

        if low_price > min(open_price, close_price, high_price):
            raise CandleValidationError(
                f"low در کندل شماره {index} با قیمت‌های OHLC سازگار نیست."
            )

    @staticmethod
    def _validate_timestamp_order(
        previous_timestamp: int,
        current_timestamp: int,
        index: int,
    ) -> None:
        """کنترل یکتا و صعودی بودن زمان کندل‌ها."""
        if current_timestamp == previous_timestamp:
            raise CandleValidationError(
                f"timestamp کندل شماره {index} تکراری است."
            )

        if current_timestamp < previous_timestamp:
            raise CandleValidationError(
                f"timestamp کندل شماره {index} باید از کندل قبلی بزرگ‌تر باشد."
            )

    @staticmethod
    def _validate_continuity(
        previous_timestamp: int,
        current_timestamp: int,
        interval_ms: int,
        index: int,
    ) -> None:
        """کنترل فاصلهٔ دقیق زمانی بین دو کندل متوالی."""
        actual_interval = current_timestamp - previous_timestamp

        if actual_interval != interval_ms:
            raise CandleValidationError(
                f"فاصلهٔ زمانی کندل شماره {index} نامعتبر است: "
                f"{actual_interval}ms؛ مقدار مورد انتظار {interval_ms}ms است."
            )

    def _resolve_timeframe(self, timeframe: str | None) -> int | None:
        """تبدیل timeframe معتبر به میلی‌ثانیه."""
        if timeframe is None:
            return None

        if not isinstance(timeframe, str):
            raise CandleValidationError("timeframe باید رشته‌ای مانند 1m یا 1h باشد.")

        normalized_timeframe = timeframe.strip().lower()

        if normalized_timeframe not in self.TIMEFRAME_TO_MS:
            supported = ", ".join(self.TIMEFRAME_TO_MS.keys())
            raise CandleValidationError(
                f"timeframe نامعتبر است: {timeframe}. "
                f"مقادیر مجاز: {supported}"
            )

        return self.TIMEFRAME_TO_MS[normalized_timeframe]
