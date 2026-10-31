import pytest
from unittest.mock import MagicMock
from src.exchange.wallex_balance_syncer import WallexBalanceSyncer

def test_stage27_balance_syncer_parses_wallex_response():
    mock_client = MagicMock()
    mock_client.get_balance.return_value = {
        "success": True,
        "result": {
            "balances": {
                "TMN": {"value": "5000000.0", "locked": "0.0"},
                "USDT": {"value": "150.25", "locked": "10.0"},
                "BTC": {"value": "0.015", "locked": "0.0"}
            }
        }
    }

    syncer = WallexBalanceSyncer(mock_client)
    balances = syncer.fetch_balances()

    assert balances["TMN"] == 5000000.0
    assert balances["USDT"] == 150.25
    assert balances["BTC"] == 0.015
    assert syncer.get_available("TMN") == 5000000.0
    assert syncer.get_available("USDT") == 150.25

def test_stage27_balance_syncer_sufficient_balance_check():
    mock_client = MagicMock()
    mock_client.get_balance.return_value = {
        "success": True,
        "result": {
            "balances": {
                "TMN": 10000000.0,
                "USDT": 200.0
            }
        }
    }

    syncer = WallexBalanceSyncer(mock_client)
    syncer.fetch_balances()

    assert syncer.has_sufficient_balance("TMN", 5000000.0) is True
    assert syncer.has_sufficient_balance("TMN", 15000000.0) is False
    assert syncer.has_sufficient_balance("USDT", 200.0) is True
    assert syncer.has_sufficient_balance("USDT", 200.1) is False
    assert syncer.has_sufficient_balance("ETH", 1.0) is False
    assert syncer.has_sufficient_balance("TMN", 0.0) is False

def test_stage27_balance_syncer_error_handling_fallback():
    mock_client = MagicMock()
    mock_client.get_balance.side_effect = Exception("Connection timeout")

    syncer = WallexBalanceSyncer(mock_client)
    balances = syncer.fetch_balances()

    assert balances == {}
    assert syncer.get_available("TMN") == 0.0
    assert syncer.has_sufficient_balance("TMN", 100.0) is False
