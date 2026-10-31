import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_pipeline import WallexLivePipeline

def test_stage28_pipeline_blocks_insufficient_buy():
    mock_executor = MagicMock()
    mock_syncer = MagicMock()
    
    # Setup: 100 USDT available, try to buy 1000 USDT worth of BTC
    mock_syncer.fetch_balances.return_value = {"USDT": 100.0, "BTC": 0.0}
    mock_syncer.has_sufficient_balance.return_value = False
    
    pipeline = WallexLivePipeline(executor=mock_executor, syncer=mock_syncer)
    result = pipeline.execute_order_with_balance_check("BTC/USDT", "BUY", 0.1, 50000.0)
    
    assert result["success"] is False
    assert result["error"] == "Insufficient funds"
    mock_executor.place_order.assert_not_called()

def test_stage28_pipeline_allows_valid_buy():
    mock_executor = MagicMock()
    mock_syncer = MagicMock()
    
    mock_syncer.fetch_balances.return_value = {"USDT": 60000.0, "BTC": 0.0}
    mock_syncer.has_sufficient_balance.return_value = True
    mock_executor.place_order.return_value = {"success": True, "order_id": "123"}
    
    pipeline = WallexLivePipeline(executor=mock_executor, syncer=mock_syncer)
    result = pipeline.execute_order_with_balance_check("BTC/USDT", "BUY", 1.0, 50000.0)
    
    assert result["success"] is True
    mock_executor.place_order.assert_called_once()
