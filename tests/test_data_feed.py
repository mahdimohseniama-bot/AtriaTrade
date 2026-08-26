import pytest

from src.data.market_fetcher import MarketFetcher
from src.data.candle_validator import CandleValidator
from src.data.data_feed import DataFeedManager


@pytest.fixture
def data_feed():
    """محیط ایزوله Paper Trading برای تست."""
    fetcher = MarketFetcher(use_paper_trading=True)
    validator = CandleValidator(max_candles=5000)

    return DataFeedManager(
        fetcher=fetcher,
        validator=validator,
        exchange_name="binance",
        max_buffer_size=50,
    )


def test_update_and_get_candles(data_feed):
    """چرخه کامل دریافت، اعتبارسنجی و ذخیره‌سازی."""
    data_feed.update_data("BTCUSDT", "15m", limit=10)

    candles = data_feed.get_candles("BTCUSDT", "15m")

    assert len(candles) == 10
    assert "timestamp" in candles[0]
    assert "open" in candles[0]
    assert "high" in candles[0]
    assert "low" in candles[0]
    assert "close" in candles[0]
    assert "volume" in candles[0]


def test_get_latest_candle(data_feed):
    """باید آخرین کندل بافر را برگرداند."""
    data_feed.update_data("ETHUSDT", "1h", limit=5)

    candles = data_feed.get_candles("ETHUSDT", "1h")
    latest = data_feed.get_latest_candle("ETHUSDT", "1h")

    assert latest is not None
    assert latest == candles[-1]
    assert "close" in latest
    assert "high" in latest


def test_buffer_size_limit(data_feed):
    """بافر نباید از سقف مشخص‌شده بزرگ‌تر شود."""
    data_feed.update_data("BTCUSDT", "1m", limit=100)

    candles = data_feed.get_candles("BTCUSDT", "1m")

    assert len(candles) == 50


def test_empty_feed_returns_empty_and_none(data_feed):
    """دریافت داده‌ای که هنوز در بافر نیست باید ایمن باشد."""
    assert data_feed.get_candles("XRPUSDT", "1d") == []
    assert data_feed.get_latest_candle("XRPUSDT", "1d") is None


def test_empty_exchange_name_is_rejected():
    """نام صرافی خالی نباید پذیرفته شود."""
    fetcher = MarketFetcher(use_paper_trading=True)
    validator = CandleValidator(max_candles=5000)

    with pytest.raises(ValueError, match="exchange_name"):
        DataFeedManager(
            fetcher=fetcher,
            validator=validator,
            exchange_name="",
        )
