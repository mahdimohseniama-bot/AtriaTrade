from copy import deepcopy

import pytest

from src.analysis.indicator_engine import IndicatorEngine


def make_candles(count=60):
    """
    تولید کندل مصنوعی برای تست‌های Backtesting/Paper Trading.
    قیمت‌ها پیوسته صعودی‌اند و از API واقعی دریافت نمی‌شوند.
    """
    candles = []

    for index in range(count):
        close = 100.0 + index

        candles.append(
            {
                "timestamp": 1_700_000_000_000 + (index * 60_000),
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 10.0 + index,
            }
        )

    return candles


def test_sma_calculation():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]

    result = IndicatorEngine.calculate_sma(values, period=3)

    assert result == [None, None, 2.0, 3.0, 4.0]


def test_ema_initializes_with_sma():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]

    result = IndicatorEngine.calculate_ema(values, period=3)

    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(2.0)
    assert result[3] == pytest.approx(3.0)
    assert result[4] == pytest.approx(4.0)


def test_rsi_of_continuously_rising_prices_is_100():
    closes = [float(value) for value in range(1, 25)]

    result = IndicatorEngine.calculate_rsi(closes, period=14)

    assert result[:14] == [None] * 14
    assert result[14] == pytest.approx(100.0)
    assert result[-1] == pytest.approx(100.0)


def test_bollinger_bands_for_constant_prices():
    closes = [100.0] * 5

    middle, upper, lower = IndicatorEngine.calculate_bollinger_bands(
        closes,
        period=5,
        std_dev_multiplier=2.0,
    )

    assert middle == [None, None, None, None, 100.0]
    assert upper == [None, None, None, None, 100.0]
    assert lower == [None, None, None, None, 100.0]


def test_atr_uses_true_range_and_wilder_smoothing():
    highs = [10.0, 12.0, 13.0, 15.0]
    lows = [8.0, 9.0, 10.0, 11.0]
    closes = [9.0, 11.0, 12.0, 14.0]

    result = IndicatorEngine.calculate_atr(
        highs,
        lows,
        closes,
        period=2,
    )

    # TR candle 1 = 3, TR candle 2 = 3 => ATR index 2 = 3
    # TR candle 3 = 4 => ATR index 3 = ((3 * 1) + 4) / 2 = 3.5
    assert result == [None, None, pytest.approx(3.0), pytest.approx(3.5)]


def test_macd_signal_starts_after_required_history():
    closes = [float(value) for value in range(1, 50)]

    macd, signal, histogram = IndicatorEngine.calculate_macd(
        closes,
        fast_period=3,
        slow_period=6,
        signal_period=4,
    )

    assert macd[4] is None
    assert macd[5] is not None

    # نخستین Signal پس از چهار مقدار معتبر MACD ایجاد می‌شود.
    assert signal[7] is None
    assert signal[8] is not None
    assert histogram[8] is not None


def test_calculate_enriches_candles_without_mutating_input():
    candles = make_candles(30)
    original_candles = deepcopy(candles)

    engine = IndicatorEngine(
        {
            "sma_periods": (3, 5),
            "ema_periods": (3, 5),
            "rsi_period": 3,
            "macd_fast_period": 3,
            "macd_slow_period": 5,
            "macd_signal_period": 2,
            "bollinger_period": 3,
            "atr_period": 3,
        }
    )

    result = engine.calculate(candles)

    assert candles == original_candles
    assert len(result) == len(candles)
    assert "indicators" not in candles[-1]

    indicators = result[-1]["indicators"]

    assert indicators["sma_3"] == pytest.approx(128.0)
    assert indicators["ema_3"] is not None
    assert indicators["rsi"] == pytest.approx(100.0)
    assert indicators["macd"] is not None
    assert indicators["macd_signal"] is not None
    assert indicators["macd_histogram"] is not None
    assert indicators["bollinger_middle"] == pytest.approx(128.0)
    assert indicators["bollinger_upper"] is not None
    assert indicators["bollinger_lower"] is not None
    assert indicators["atr"] is not None


def test_insufficient_history_returns_none_values():
    candles = make_candles(3)

    engine = IndicatorEngine(
        {
            "sma_periods": (5,),
            "ema_periods": (5,),
            "rsi_period": 5,
            "macd_fast_period": 2,
            "macd_slow_period": 3,
            "macd_signal_period": 3,
            "bollinger_period": 5,
            "atr_period": 5,
        }
    )

    result = engine.calculate(candles)

    last_indicators = result[-1]["indicators"]

    assert last_indicators["sma_5"] is None
    assert last_indicators["ema_5"] is None
    assert last_indicators["rsi"] is None
    assert last_indicators["macd"] is not None
    assert last_indicators["macd_signal"] is None
    assert last_indicators["macd_histogram"] is None
    assert last_indicators["bollinger_middle"] is None
    assert last_indicators["atr"] is None


def test_invalid_candle_is_rejected():
    engine = IndicatorEngine()

    invalid_candles = [
        {
            "open": 100.0,
            "high": 90.0,
            "low": 95.0,
            "close": 96.0,
        }
    ]

    with pytest.raises(ValueError, match="high lower than low"):
        engine.calculate(invalid_candles)


def test_invalid_macd_configuration_is_rejected():
    with pytest.raises(
        ValueError,
        match="macd_fast_period must be smaller",
    ):
        IndicatorEngine(
            {
                "macd_fast_period": 26,
                "macd_slow_period": 12,
            }
        )
