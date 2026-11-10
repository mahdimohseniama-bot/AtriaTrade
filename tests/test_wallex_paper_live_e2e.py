import pytest
from unittest.mock import MagicMock, patch
from scripts.run_wallex_paper_live import run_loop

def test_wallex_paper_live_e2e_buy_and_exit():
    # Mock WallexPaperAdapter
    mock_adapter = MagicMock()
    # Cycle 1: Price 65000 (Triggers BUY)
    # Cycle 2: Price 67000 (Triggers TP Exit -> SELL)
    mock_adapter.get_ticker.side_effect = [
        {"price": 65000.0},
        {"price": 67000.0},
        {"price": 67000.0}
    ]
    mock_adapter.place_order.side_effect = [
        {"order_id": "ord_buy_1", "status": "FILLED"},
        {"order_id": "ord_tp_exit", "status": "FILLED"}
    ]

    # Mock RiskManager
    mock_risk = MagicMock()
    mock_risk.can_trade_today.return_value = True

    # Mock Strategy: BUY on first call, HOLD afterwards
    mock_strat = MagicMock()
    mock_strat.generate_signal.side_effect = ["BUY", "HOLD", "HOLD"]

    # Mock time.time to simulate cycle 1 (0s), cycle 2 (2s), then loop finish (5s)
    simulated_times = [0.0, 0.1, 2.0, 2.1, 5.0, 5.1]
    
    with patch("scripts.run_wallex_paper_live.WallexPaperAdapter", return_value=mock_adapter), \
         patch("scripts.run_wallex_paper_live.RiskManager", return_value=mock_risk), \
         patch("scripts.run_wallex_paper_live.SMACrossStrategy", return_value=mock_strat), \
         patch("time.time", side_effect=simulated_times), \
         patch("time.sleep", return_value=None):
        
        run_loop(duration_seconds=4, interval_seconds=2, symbol="BTCUSDT")

    # Assertions
    assert mock_adapter.place_order.call_count == 2
    # Verify first order was BUY
    first_order_kwargs = mock_adapter.place_order.call_args_list[0].kwargs
    assert first_order_kwargs["side"] == "buy"
    # Verify second order was SELL (TP exit)
    second_order_kwargs = mock_adapter.place_order.call_args_list[1].kwargs
    assert second_order_kwargs["side"] == "sell"
