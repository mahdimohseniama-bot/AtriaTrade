"""Unit tests for Paper Exchange Factory."""

import pytest
from src.adapters.paper_factory import PaperExchangeFactory
from src.adapters.nobitex_paper import NobitexPaperAdapter
from src.adapters.wallex_paper import WallexPaperAdapter


def test_create_nobitex_adapter():
    adapter = PaperExchangeFactory.create_adapter("nobitex", {"rls": 100_000_000, "usdt": 500})
    assert isinstance(adapter, NobitexPaperAdapter)
    assert adapter.get_balance("rls") == 100_000_000
    assert adapter.get_balance("usdt") == 500


def test_create_wallex_adapter():
    adapter = PaperExchangeFactory.create_adapter("wallex", {"tm": 20_000_000, "btc": 0.2})
    assert isinstance(adapter, WallexPaperAdapter)
    assert adapter.get_balance("tm") == 20_000_000
    assert adapter.get_balance("btc") == 0.2


def test_unsupported_exchange_raises_error():
    with pytest.raises(ValueError) as excinfo:
        PaperExchangeFactory.create_adapter("unknown_exchange")
    assert "Unsupported paper exchange" in str(excinfo.value)
