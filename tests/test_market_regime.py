"""Unit tests for MarketRegimeFilter (Pure Python)."""

import pytest
from src.core.market_regime import MarketRegimeFilter, MarketRegime


def generate_candles(start_price: float, step: float, count: int, spread: float = 1.0):
    candles = []
    p = start_price
    for _ in range(count):
        candles.append({
            "open": p,
            "high": p + spread,
            "low": p - spread,
            "close": p,
            "volume": 100
        })
        p += step
    return candles


def test_insufficient_data():
    mrf = MarketRegimeFilter(fast_window=5, slow_window=10)
    candles = generate_candles(100.0, 1.0, 5)
    res = mrf.detect_regime(candles)
    assert res["regime"] == MarketRegime.UNKNOWN


def test_bull_trend_detection():
    mrf = MarketRegimeFilter(fast_window=5, slow_window=15, trend_threshold_pct=0.01)
    # کندل‌های شدیداً صعودی
    candles = generate_candles(100.0, 2.0, 20, spread=0.5)
    res = mrf.detect_regime(candles)
    assert res["regime"] == MarketRegime.BULL_TREND
    assert mrf.should_allow_signal(res["regime"], "BUY") is True
    assert mrf.should_allow_signal(res["regime"], "SELL") is False


def test_bear_trend_detection():
    mrf = MarketRegimeFilter(fast_window=5, slow_window=15, trend_threshold_pct=0.01)
    # کندل‌های نزولی
    candles = generate_candles(200.0, -2.0, 20, spread=0.5)
    res = mrf.detect_regime(candles)
    assert res["regime"] == MarketRegime.BEAR_TREND
    assert mrf.should_allow_signal(res["regime"], "SELL") is True
    assert mrf.should_allow_signal(res["regime"], "BUY") is False


def test_ranging_detection():
    mrf = MarketRegimeFilter(fast_window=5, slow_window=15, trend_threshold_pct=0.05)
    # کندل‌های فلت و بدون روند
    candles = generate_candles(100.0, 0.0, 20, spread=0.5)
    res = mrf.detect_regime(candles)
    assert res["regime"] == MarketRegime.RANGING
    assert mrf.should_allow_signal(res["regime"], "BUY") is True
    assert mrf.should_allow_signal(res["regime"], "SELL") is True


def test_high_volatility_blocks_trading():
    mrf = MarketRegimeFilter(fast_window=5, slow_window=15, volatility_threshold_pct=0.03)
    # نوسان خیلی شدید (اسپرد ۱۰ روی قیمت ۱۰۰ = ۱۰٪ نوسان)
    candles = generate_candles(100.0, 0.5, 20, spread=10.0)
    res = mrf.detect_regime(candles)
    assert res["regime"] == MarketRegime.HIGH_VOLATILITY
    assert mrf.should_allow_signal(res["regime"], "BUY") is False
    assert mrf.should_allow_signal(res["regime"], "SELL") is False
