import pytest
from unittest.mock import MagicMock, patch
from scripts.run_wallex_paper import run_wallex_paper_live

@patch("src.adapters.wallex_paper.requests.get")
def test_run_wallex_paper_live_smoke(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "bid": [{"price": 610000.0, "quantity": 1.0}],
            "ask": [{"price": 611000.0, "quantity": 1.0}]
        }
    }
    mock_get.return_value = mock_resp

    # Run for 2 iterations with 0 sleep to verify no crashes
    run_wallex_paper_live(symbol="USDTTMN", iterations=2, sleep_sec=0)
