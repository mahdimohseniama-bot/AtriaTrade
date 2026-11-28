import pytest
from unittest.mock import MagicMock, patch
from src.adapters.paper_factory import PaperExchangeFactory
from src.strategies.sma_cross_strategy import SMACrossStrategy

@patch("src.adapters.wallex_paper.requests.get")
def test_wallex_sma_cross_flow(mock_get):
    # Mock Wallex Orderbook response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "bid": [{"price": 650000.0, "quantity": 2.0}],
            "ask": [{"price": 651000.0, "quantity": 1.5}]
        }
    }
    mock_get.return_value = mock_resp

    # Initialize paper adapter for Wallex
    adapter = PaperExchangeFactory.create_adapter("wallex")
    strategy = SMACrossStrategy(fast_period=3, slow_period=5)

    # Simulated prices triggering a golden cross using on_tick
    price_series = [600000.0, 605000.0, 610000.0, 620000.0, 630000.0, 650000.0]
    
    signal = None
    for p in price_series:
        tick = {"price": p, "volume": 10.0}
        sig = strategy.on_tick(tick)
        if sig:
            signal = sig

    # Ensure bullish cross was detected
    assert signal is not None
    # Depending on implementation, action can be returned as string or dict
    action = signal.get("action") if isinstance(signal, dict) else signal
    assert action in ["buy", "BUY"]

    # Execute paper trade based on signal
    initial_usdt = adapter.get_balance("USDT")
    res = adapter.place_order(
        symbol="USDTTMN",
        side="buy",
        order_type="market",
        amount=1.0
    )

    assert res["status"] == "success"
    assert res["result"]["status"] == "FILLED"
    assert adapter.get_balance("USDT") == initial_usdt + 1.0
