import pytest
from unittest.mock import MagicMock, patch
from src.core.paper_live_runner import PaperLiveRunner
from src.adapters.wallex_data_feed import WallexDataFeed
from src.adapters.wallex_paper import WallexPaperAdapter

def test_paper_live_runner_with_wallex_feed_tick():
    mock_feed = MagicMock(spec=WallexDataFeed)
    mock_feed.get_ticker_price.return_value = 289374.0
    mock_feed.get_orderbook.return_value = {
        "status": "success",
        "data": {
            "bid": [{"price": 289300.0, "quantity": 100.0}],
            "ask": [{"price": 289450.0, "quantity": 100.0}]
        }
    }
    
    adapter = WallexPaperAdapter(initial_tmn=10_000_000, initial_usdt=0)
    
    runner = PaperLiveRunner(
        adapter=adapter,
        symbol="USDTTMN",
        data_feed=mock_feed,
        interval_seconds=1
    )
    
    assert runner.symbol == "USDTTMN"
    assert runner.data_feed is not None
    
    # Run a single tick iteration
    result = runner.run_single_tick()
    assert result["status"] == "success"
    assert result["mid_price"] == 289374.0
    assert result["orders_count"] == 0

def test_paper_live_runner_feed_failure_handling():
    mock_feed = MagicMock(spec=WallexDataFeed)
    mock_feed.get_ticker_price.return_value = None
    
    adapter = WallexPaperAdapter(initial_tmn=10_000_000, initial_usdt=0)
    runner = PaperLiveRunner(
        adapter=adapter,
        symbol="USDTTMN",
        data_feed=mock_feed,
        interval_seconds=1
    )
    
    result = runner.run_single_tick()
    assert result["status"] == "skipped"
    assert "Price feed unavailable" in result["reason"]
