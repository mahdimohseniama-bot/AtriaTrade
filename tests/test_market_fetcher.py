import pytest
from src.data.market_fetcher import MarketFetcher

def test_market_fetcher_initialization():
    fetcher = MarketFetcher(use_paper_trading=True)
    assert fetcher.use_paper_trading is True

def test_fetch_ohlcv_returns_correct_limit():
    fetcher = MarketFetcher(use_paper_trading=True)
    data = fetcher.fetch_ohlcv("BINANCE", "BTCUSDT", "1m", limit=50)
    assert len(data) == 50

def test_fetch_ohlcv_contains_required_keys():
    fetcher = MarketFetcher(use_paper_trading=True)
    data = fetcher.fetch_ohlcv("NOBITEX", "ETHUSDT", "1h", limit=1)
    assert len(data) == 1
    candle = data[0]
    
    expected_keys = {"timestamp", "open", "high", "low", "close", "volume"}
    assert set(candle.keys()) == expected_keys

def test_fetch_ohlcv_invalid_limit_raises_error():
    fetcher = MarketFetcher(use_paper_trading=True)
    with pytest.raises(ValueError, match="Limit must be a positive integer."):
        fetcher.fetch_ohlcv("BINANCE", "BTCUSDT", "1m", limit=-5)

def test_fetch_ohlcv_empty_symbol_raises_error():
    fetcher = MarketFetcher(use_paper_trading=True)
    with pytest.raises(ValueError, match="Symbol and timeframe cannot be empty."):
        fetcher.fetch_ohlcv("BINANCE", "", "1m")

def test_live_data_raises_not_implemented():
    fetcher = MarketFetcher(use_paper_trading=False)
    with pytest.raises(NotImplementedError, match="Live data fetching is disabled."):
        fetcher.fetch_ohlcv("BINANCE", "BTCUSDT", "1m")
