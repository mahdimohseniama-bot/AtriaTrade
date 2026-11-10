import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_runner import WallexLiveRunner

@pytest.fixture
def mock_exec_engine():
    engine = MagicMock()
    engine.execute_live_order.return_value = {
        "status": "EXECUTED",
        "symbol": "BTCUSDT",
        "quantity": 0.05,
        "price": 100.0
    }
    return engine

@pytest.fixture
def mock_recon_engine():
    engine = MagicMock()
    engine.reconcile_balances.return_value = {
        "synced": True,
        "remote_balance": 15.0,
        "status": "SYNCED"
    }
    return engine

def test_runner_cycle_success(mock_exec_engine, mock_recon_engine):
    runner = WallexLiveRunner(mock_exec_engine, mock_recon_engine)
    res = runner.execute_cycle(
        symbol="BTCUSDT",
        side="BUY",
        local_balance=15.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        orderbook={"bids": [[100, 1]], "asks": [[100.1, 1]]},
        reference_price=100.0
    )
    assert res["status"] == "COMPLETED"
    assert res["execution"]["status"] == "EXECUTED"
    mock_recon_engine.reconcile_balances.assert_called_once()
    mock_exec_engine.execute_live_order.assert_called_once()

def test_runner_cycle_aborted_on_desync(mock_exec_engine, mock_recon_engine):
    mock_recon_engine.reconcile_balances.return_value = {
        "synced": False,
        "status": "BALANCE_MISMATCH"
    }
    runner = WallexLiveRunner(mock_exec_engine, mock_recon_engine)
    res = runner.execute_cycle(
        symbol="BTCUSDT",
        side="BUY",
        local_balance=15.0,
        entry_price=100.0,
        stop_loss_price=95.0,
        orderbook={},
        reference_price=100.0
    )
    assert res["status"] == "ABORTED"
    assert res["phase"] == "RECONCILIATION"
    mock_exec_engine.execute_live_order.assert_not_called()
