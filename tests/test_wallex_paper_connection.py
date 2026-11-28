import pytest
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_paper_initialization():
    adapter = WallexPaperAdapter()
    assert adapter is not None
    assert hasattr(adapter, "place_order")
    assert hasattr(adapter, "get_balance")

def test_wallex_paper_symbol_normalization():
    adapter = WallexPaperAdapter()
    normalized = adapter.normalize_symbol("btc-usdt")
    assert normalized == "BTC-USDT"
