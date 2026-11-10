import pytest
from unittest.mock import MagicMock, patch
from scripts.run_wallex_paper_live import run_loop

def test_runner_dispatches_alerts_on_trade_events():
    mock_adapter = MagicMock()
    mock_adapter.get_ticker.side_effect = [
        {"price": 60000.0},
        {"price": 62000.0}
    ]
    mock_adapter.place_order.return_value = {"order_id": "test_ord", "status": "FILLED"}

    mock_risk = MagicMock()
    mock_risk.can_trade_today.return_value = True

    mock_strat = MagicMock()
    mock_strat.generate_signal.side_effect = ["BUY", "HOLD"]

    mock_notifier = MagicMock()

    simulated_times = [0.0, 0.1, 2.0, 2.1, 5.0, 5.1]

    with patch("scripts.run_wallex_paper_live.WallexPaperAdapter", return_value=mock_adapter), \
         patch("scripts.run_wallex_paper_live.RiskManager", return_value=mock_risk), \
         patch("scripts.run_wallex_paper_live.SMACrossStrategy", return_value=mock_strat), \
         patch("scripts.run_wallex_paper_live.AlertNotifier", return_value=mock_notifier), \
         patch("time.time", side_effect=simulated_times), \
         patch("time.sleep", return_value=None):
        
        run_loop(duration_seconds=4, interval_seconds=2, symbol="BTCUSDT")

    # Assert that notifier was called for both BUY order and TP exit
    assert mock_notifier.notify.call_count >= 2
    alert_titles = [call.kwargs["title"] for call in mock_notifier.notify.call_args_list]
    assert "ORDER_BUY_FILLED" in alert_titles
    assert "POSITION_EXIT_TP" in alert_titles
