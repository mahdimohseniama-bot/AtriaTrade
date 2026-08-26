"""
Technical Indicator Engine for AtriaTrade.

This module is designed for Paper Trading and Backtesting workflows.
It calculates indicators from validated OHLCV candles without mutating
the original candle list.

Supported indicators:
- SMA
- EMA
- RSI (Wilder smoothing)
- MACD
- Bollinger Bands
- ATR (Wilder smoothing)
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional, Sequence


Candle = Mapping[str, Any]
IndicatorValue = Optional[float]


class IndicatorEngine:
    """
    Stateless technical-indicator calculator.

    Input candles must provide at least:
    - close: for SMA, EMA, RSI, MACD and Bollinger Bands
    - high, low, close: for ATR

    Every output row is a copy of the corresponding input candle with an
    additional `indicators` dictionary.
    """

    DEFAULT_CONFIG: Dict[str, Any] = {
        "sma_periods": (20, 50),
        "ema_periods": (12, 26),
        "rsi_period": 14,
        "macd_fast_period": 12,
        "macd_slow_period": 26,
        "macd_signal_period": 9,
        "bollinger_period": 20,
        "bollinger_std_dev": 2.0,
        "atr_period": 14,
    }

    def __init__(self, config: Optional[Mapping[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = dict(self.DEFAULT_CONFIG)

        if config:
            self.config.update(dict(config))

        self._validate_config()

    def calculate(self, candles: Sequence[Candle]) -> List[Dict[str, Any]]:
        """
        Calculate all configured indicators for candles.

        Parameters
        ----------
        candles:
            A sequence of validated OHLCV candle dictionaries.

        Returns
        -------
        list[dict]:
            Deep-copied candles, each enriched with an `indicators` key.
        """
        normalized_candles = self._normalize_candles(candles)

        if not normalized_candles:
            return []

        closes = [candle["close"] for candle in normalized_candles]
        highs = [candle["high"] for candle in normalized_candles]
        lows = [candle["low"] for candle in normalized_candles]

        sma_values = {
            period: self.calculate_sma(closes, period)
            for period in self.config["sma_periods"]
        }
        ema_values = {
            period: self.calculate_ema(closes, period)
            for period in self.config["ema_periods"]
        }

        rsi_values = self.calculate_rsi(
            closes,
            self.config["rsi_period"],
        )

        macd_line, macd_signal, macd_histogram = self.calculate_macd(
            closes,
            fast_period=self.config["macd_fast_period"],
            slow_period=self.config["macd_slow_period"],
            signal_period=self.config["macd_signal_period"],
        )

        bollinger_middle, bollinger_upper, bollinger_lower = (
            self.calculate_bollinger_bands(
                closes,
                period=self.config["bollinger_period"],
                std_dev_multiplier=self.config["bollinger_std_dev"],
            )
        )

        atr_values = self.calculate_atr(
            highs,
            lows,
            closes,
            period=self.config["atr_period"],
        )

        enriched_candles: List[Dict[str, Any]] = []

        for index, candle in enumerate(normalized_candles):
            enriched_candle = deepcopy(candle)
            indicators: Dict[str, IndicatorValue] = {
                f"sma_{period}": values[index]
                for period, values in sma_values.items()
            }
            indicators.update(
                {
                    f"ema_{period}": values[index]
                    for period, values in ema_values.items()
                }
            )
            indicators.update(
                {
                    "rsi": rsi_values[index],
                    "macd": macd_line[index],
                    "macd_signal": macd_signal[index],
                    "macd_histogram": macd_histogram[index],
                    "bollinger_middle": bollinger_middle[index],
                    "bollinger_upper": bollinger_upper[index],
                    "bollinger_lower": bollinger_lower[index],
                    "atr": atr_values[index],
                }
            )

            enriched_candle["indicators"] = indicators
            enriched_candles.append(enriched_candle)

        return enriched_candles

    @staticmethod
    def calculate_sma(
        values: Sequence[float],
        period: int,
    ) -> List[IndicatorValue]:
        """Calculate Simple Moving Average."""
        IndicatorEngine._validate_period(period, "period")

        result: List[IndicatorValue] = [None] * len(values)

        if len(values) < period:
            return result

        rolling_sum = sum(values[:period])
        result[period - 1] = rolling_sum / period

        for index in range(period, len(values)):
            rolling_sum += values[index] - values[index - period]
            result[index] = rolling_sum / period

        return result

    @staticmethod
    def calculate_ema(
        values: Sequence[float],
        period: int,
    ) -> List[IndicatorValue]:
        """
        Calculate Exponential Moving Average.

        The first valid EMA value is initialized using SMA(period).
        """
        IndicatorEngine._validate_period(period, "period")

        result: List[IndicatorValue] = [None] * len(values)

        if len(values) < period:
            return result

        multiplier = 2.0 / (period + 1)
        first_ema = sum(values[:period]) / period

        result[period - 1] = first_ema
        previous_ema = first_ema

        for index in range(period, len(values)):
            current_ema = (
                (values[index] - previous_ema) * multiplier
            ) + previous_ema

            result[index] = current_ema
            previous_ema = current_ema

        return result

    @staticmethod
    def calculate_rsi(
        closes: Sequence[float],
        period: int = 14,
    ) -> List[IndicatorValue]:
        """
        Calculate RSI using Wilder's smoothing method.

        RSI needs period + 1 close prices because the first period contains
        price changes, not candle values.
        """
        IndicatorEngine._validate_period(period, "period")

        result: List[IndicatorValue] = [None] * len(closes)

        if len(closes) <= period:
            return result

        gains: List[float] = []
        losses: List[float] = []

        for index in range(1, period + 1):
            change = closes[index] - closes[index - 1]
            gains.append(max(change, 0.0))
            losses.append(abs(min(change, 0.0)))

        average_gain = sum(gains) / period
        average_loss = sum(losses) / period

        result[period] = IndicatorEngine._rsi_from_averages(
            average_gain,
            average_loss,
        )

        for index in range(period + 1, len(closes)):
            change = closes[index] - closes[index - 1]
            gain = max(change, 0.0)
            loss = abs(min(change, 0.0))

            average_gain = (
                ((average_gain * (period - 1)) + gain) / period
            )
            average_loss = (
                ((average_loss * (period - 1)) + loss) / period
            )

            result[index] = IndicatorEngine._rsi_from_averages(
                average_gain,
                average_loss,
            )

        return result

    @staticmethod
    def calculate_macd(
        closes: Sequence[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[
        List[IndicatorValue],
        List[IndicatorValue],
        List[IndicatorValue],
    ]:
        """Calculate MACD line, signal line and histogram."""
        IndicatorEngine._validate_period(fast_period, "fast_period")
        IndicatorEngine._validate_period(slow_period, "slow_period")
        IndicatorEngine._validate_period(signal_period, "signal_period")

        if fast_period >= slow_period:
            raise ValueError(
                "fast_period must be smaller than slow_period."
            )

        fast_ema = IndicatorEngine.calculate_ema(closes, fast_period)
        slow_ema = IndicatorEngine.calculate_ema(closes, slow_period)

        macd_line: List[IndicatorValue] = [None] * len(closes)

        for index in range(len(closes)):
            fast_value = fast_ema[index]
            slow_value = slow_ema[index]

            if fast_value is not None and slow_value is not None:
                macd_line[index] = fast_value - slow_value

        signal_line = IndicatorEngine._calculate_ema_with_gaps(
            macd_line,
            signal_period,
        )

        histogram: List[IndicatorValue] = [None] * len(closes)

        for index in range(len(closes)):
            macd_value = macd_line[index]
            signal_value = signal_line[index]

            if macd_value is not None and signal_value is not None:
                histogram[index] = macd_value - signal_value

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(
        closes: Sequence[float],
        period: int = 20,
        std_dev_multiplier: float = 2.0,
    ) -> tuple[
        List[IndicatorValue],
        List[IndicatorValue],
        List[IndicatorValue],
    ]:
        """Calculate Bollinger middle, upper and lower bands."""
        IndicatorEngine._validate_period(period, "period")

        if not isinstance(std_dev_multiplier, (int, float)):
            raise ValueError("std_dev_multiplier must be numeric.")

        if std_dev_multiplier <= 0:
            raise ValueError("std_dev_multiplier must be greater than zero.")

        middle: List[IndicatorValue] = [None] * len(closes)
        upper: List[IndicatorValue] = [None] * len(closes)
        lower: List[IndicatorValue] = [None] * len(closes)

        if len(closes) < period:
            return middle, upper, lower

        for index in range(period - 1, len(closes)):
            window = closes[index - period + 1:index + 1]
            mean = sum(window) / period
            variance = sum((value - mean) ** 2 for value in window) / period
            standard_deviation = math.sqrt(variance)

            middle[index] = mean
            upper[index] = mean + (std_dev_multiplier * standard_deviation)
            lower[index] = mean - (std_dev_multiplier * standard_deviation)

        return middle, upper, lower

    @staticmethod
    def calculate_atr(
        highs: Sequence[float],
        lows: Sequence[float],
        closes: Sequence[float],
        period: int = 14,
    ) -> List[IndicatorValue]:
        """
        Calculate ATR using Wilder's smoothing method.

        ATR begins at index `period` because the initial value uses
        true ranges from candles index 1 through index period.
        """
        IndicatorEngine._validate_period(period, "period")

        if not (len(highs) == len(lows) == len(closes)):
            raise ValueError(
                "highs, lows and closes must have the same length."
            )

        result: List[IndicatorValue] = [None] * len(closes)

        if len(closes) <= period:
            return result

        true_ranges: List[float] = []

        for index in range(1, len(closes)):
            true_range = max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
            true_ranges.append(true_range)

        first_atr = sum(true_ranges[:period]) / period
        result[period] = first_atr
        previous_atr = first_atr

        for index in range(period + 1, len(closes)):
            current_true_range = true_ranges[index - 1]
            current_atr = (
                ((previous_atr * (period - 1)) + current_true_range)
                / period
            )
            result[index] = current_atr
            previous_atr = current_atr

        return result

    def _validate_config(self) -> None:
        """Validate all engine configuration values."""
        for period in self.config["sma_periods"]:
            self._validate_period(period, "sma_periods item")

        for period in self.config["ema_periods"]:
            self._validate_period(period, "ema_periods item")

        self._validate_period(self.config["rsi_period"], "rsi_period")
        self._validate_period(
            self.config["macd_fast_period"],
            "macd_fast_period",
        )
        self._validate_period(
            self.config["macd_slow_period"],
            "macd_slow_period",
        )
        self._validate_period(
            self.config["macd_signal_period"],
            "macd_signal_period",
        )
        self._validate_period(
            self.config["bollinger_period"],
            "bollinger_period",
        )
        self._validate_period(self.config["atr_period"], "atr_period")

        if (
            self.config["macd_fast_period"]
            >= self.config["macd_slow_period"]
        ):
            raise ValueError(
                "macd_fast_period must be smaller than macd_slow_period."
            )

        multiplier = self.config["bollinger_std_dev"]

        if not isinstance(multiplier, (int, float)) or multiplier <= 0:
            raise ValueError(
                "bollinger_std_dev must be a positive number."
            )

    @staticmethod
    def _normalize_candles(
        candles: Sequence[Candle],
    ) -> List[Dict[str, Any]]:
        """
        Validate and normalize candle values without changing caller data.
        """
        if candles is None:
            raise ValueError("candles cannot be None.")

        normalized: List[Dict[str, Any]] = []

        for index, raw_candle in enumerate(candles):
            if not isinstance(raw_candle, Mapping):
                raise ValueError(
                    f"Candle at index {index} must be a mapping."
                )

            candle = dict(raw_candle)
            required_fields = ("high", "low", "close")

            for field in required_fields:
                if field not in candle:
                    raise ValueError(
                        f"Candle at index {index} is missing '{field}'."
                    )

                try:
                    candle[field] = float(candle[field])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Candle at index {index} has invalid '{field}'."
                    ) from exc

                if not math.isfinite(candle[field]):
                    raise ValueError(
                        f"Candle at index {index} has non-finite '{field}'."
                    )

            if candle["high"] < candle["low"]:
                raise ValueError(
                    f"Candle at index {index} has high lower than low."
                )

            if not candle["low"] <= candle["close"] <= candle["high"]:
                raise ValueError(
                    f"Candle at index {index} has close outside high-low range."
                )

            normalized.append(candle)

        return normalized

    @staticmethod
    def _calculate_ema_with_gaps(
        values: Sequence[IndicatorValue],
        period: int,
    ) -> List[IndicatorValue]:
        """
        Calculate EMA while preserving the original sequence indexes.

        Used for MACD signal line, where MACD starts after slow EMA becomes
        available.
        """
        IndicatorEngine._validate_period(period, "period")

        result: List[IndicatorValue] = [None] * len(values)
        valid_indexes = [
            index for index, value in enumerate(values)
            if value is not None
        ]

        if len(valid_indexes) < period:
            return result

        first_indexes = valid_indexes[:period]
        first_ema = sum(
            float(values[index])
            for index in first_indexes
        ) / period

        first_output_index = first_indexes[-1]
        result[first_output_index] = first_ema

        multiplier = 2.0 / (period + 1)
        previous_ema = first_ema

        for index in valid_indexes[period:]:
            current_value = float(values[index])
            current_ema = (
                (current_value - previous_ema) * multiplier
            ) + previous_ema

            result[index] = current_ema
            previous_ema = current_ema

        return result

    @staticmethod
    def _rsi_from_averages(
        average_gain: float,
        average_loss: float,
    ) -> float:
        """Convert Wilder average gain/loss values into RSI."""
        if average_loss == 0:
            return 100.0 if average_gain > 0 else 50.0

        if average_gain == 0:
            return 0.0

        relative_strength = average_gain / average_loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    @staticmethod
    def _validate_period(value: Any, name: str) -> None:
        """Validate integer indicator periods."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be a positive integer.")

        if value <= 0:
            raise ValueError(f"{name} must be a positive integer.")
