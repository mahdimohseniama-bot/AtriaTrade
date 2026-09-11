from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from src.data.market_fetcher import MarketFetcher


def test_market_fetcher_initialization():
    fetcher = MarketFetcher(use_paper_trading=True)
    assert fetcher.use_paper_trading is True
    assert fetcher.timeout == 10


def test_fetch_ohlcv_returns_correct_limit_mock():
    fetcher = MarketFetcher(use_paper_trading=True)
    data = fetcher.fetch_ohlcv("WALLEX", "BTCUSDT", "1m", limit=50)
    assert len(data) == 50


def test_fetch_ohlcv_contains_required_keys():
    fetcher = MarketFetcher(use_paper_trading=True)
    data = fetcher.fetch_ohlcv("WALLEX", "ETHUSDT", "1h", limit=1)
    assert len(data) == 1
    candle = data[0]

    expected_keys = {"timestamp", "open", "high", "low", "close", "volume"}
    assert set(candle.keys()) == expected_keys


def test_fetch_ohlcv_invalid_limit_raises_error():
    fetcher = MarketFetcher(use_paper_trading=True)
    with pytest.raises(ValueError, match="Limit must be a positive integer."):
        fetcher.fetch_ohlcv("WALLEX", "BTCUSDT", "1m", limit=-5)


def test_fetch_ohlcv_empty_symbol_raises_error():
    fetcher = MarketFetcher(use_paper_trading=True)
    with pytest.raises(ValueError, match="Symbol and timeframe cannot be empty."):
        fetcher.fetch_ohlcv("WALLEX", "", "1m")


def test_fetch_ohlcv_unsupported_exchange_raises_not_implemented():
    fetcher = MarketFetcher(use_paper_trading=False)
    with pytest.raises(NotImplementedError, match="Live data fetching for UNKNOWN is not implemented."):
        fetcher.fetch_ohlcv("UNKNOWN", "BTCUSDT", "1m")


@patch("urllib.request.urlopen")
def test_wallex_live_fetch_success(mock_urlopen):
    # شبیه‌سازی پاسخ موفق UDF والکس
    mock_response = MagicMock()
    mock_response.status = 200
    mock_payload = {
        "s": "ok",
        "t": [1700000000, 1700000060],
        "o": [65000.0, 65100.0],
        "h": [65200.0, 65300.0],
        "l": [64900.0, 65050.0],
        "c": [65100.0, 65250.0],
        "v": [12.5, 15.2],
    }
    mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    fetcher = MarketFetcher(use_paper_trading=False)
    candles = fetcher.fetch_ohlcv("WALLEX", "BTCUSDT", "1m", limit=2)

    assert len(candles) == 2
    assert candles[0]["timestamp"] == 1700000000 * 1000
    assert candles[0]["close"] == 65100.0
    assert candles[1]["high"] == 65300.0
