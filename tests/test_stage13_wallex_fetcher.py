import sys
from unittest.mock import patch, MagicMock
from src.exchange.wallex_orderbook_fetcher import WallexOrderbookFetcher

def test_stage13():
    print("[STAGE 13] WALLEX RESILIENT ORDERBOOK FETCHER TEST STARTING...")
    fetcher = WallexOrderbookFetcher(timeout_sec=1.0, max_retries=2)

    # Test Case 1: Mocked successful Wallex response
    mock_resp_success = MagicMock()
    mock_resp_success.status_code = 200
    mock_resp_success.json.return_value = {
        "result": {
            "bid": [{"price": "1000000.0", "quantity": "0.5"}],
            "ask": [{"price": "1002000.0", "quantity": "0.3"}]
        }
    }

    with patch("requests.get", return_value=mock_resp_success):
        res = fetcher.fetch_orderbook("TMNUSDT")
        assert res["success"] is True
        assert res["best_bid"] == 1000000.0
        assert res["best_ask"] == 1002000.0

    # Test Case 2: Network failure / timeout triggering retry and failure response
    with patch("requests.get", side_effect=Exception("Connection timed out")):
        res_fail = fetcher.fetch_orderbook("TMNUSDT")
        assert res_fail["success"] is False
        assert res_fail["reason"] == "FETCH_FAILED_TIMEOUT_OR_NETWORK"

    # Test Case 3: Circuit breaker trip
    fetcher.consecutive_failures = 5
    res_cb = fetcher.fetch_orderbook("TMNUSDT")
    assert res_cb["success"] is False
    assert res_cb["reason"] == "CIRCUIT_BREAKER_OPEN"

    print("[SUCCESS] Stage 13 Resilient Wallex Orderbook Fetcher Passed!")

if __name__ == "__main__":
    test_stage13()
