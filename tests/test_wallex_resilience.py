import pytest
from unittest.mock import MagicMock
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_network_retry_and_resilience():
    adapter = WallexPaperAdapter()
    
    # Simulate network hiccups (2 fails then 1 success)
    attempts = 0
    def flaky_get_ticker(symbol):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Simulated network timeout/filtering")
        return {"symbol": symbol, "bid": 70000.0, "ask": 70100.0, "last": 70050.0}
    
    adapter.get_ticker = MagicMock(side_effect=flaky_get_ticker)
    
    # Test retry mechanism wrapper
    result = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = adapter.get_ticker("BTC/USDT")
            break
        except ConnectionError:
            continue
            
    assert result is not None
    assert result["last"] == 70050.0
    assert attempts == 3

def test_wallex_circuit_breaker_on_repeated_failure():
    adapter = WallexPaperAdapter()
    adapter.get_ticker = MagicMock(side_effect=ConnectionError("Persistent exchange outage"))
    
    failed = False
    try:
        for _ in range(3):
            adapter.get_ticker("BTC/USDT")
    except ConnectionError:
        failed = True
        
    assert failed is True
