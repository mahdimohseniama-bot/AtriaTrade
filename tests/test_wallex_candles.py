import pytest
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_paper_get_candles_default():
    adapter = WallexPaperAdapter()
    candles = adapter.get_candles(symbol="BTCUSDT", resolution="1m", limit=30)
    assert isinstance(candles, list)
    assert len(candles) == 30
    first = candles[0]
    for key in ["time", "open", "high", "low", "close", "volume"]:
        assert key in first
    assert first["high"] >= first["low"]

def test_wallex_paper_get_candles_limit():
    adapter = WallexPaperAdapter()
    candles = adapter.get_candles(symbol="BTCUSDT", resolution="5m", limit=15)
    assert len(candles) == 15
