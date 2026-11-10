import pytest
from unittest.mock import Mock
from src.core.network_health_monitor import NetworkHealthMonitor
from src.core.wallex_resilient_pipeline import WallexResilientPipeline

def test_pipeline_normal_order_submission():
    pipeline = WallexResilientPipeline(max_retries=2, backoff_factor=0.01)
    mock_order_api = Mock(return_value={"order_id": 8801, "status": "active"})

    res = pipeline.submit_resilient_order(
        client_order_id="CID_101",
        symbol="BTCIRT",
        side="BUY",
        price=6000000000.0,
        quantity=0.002,
        exchange_order_func=mock_order_api
    )

    assert res["status"] == "SUBMITTED"
    assert res["data"]["order_id"] == 8801
    assert pipeline.reconciler.has_pending_reconciliations() is False

def test_pipeline_fails_and_auto_reconciles():
    pipeline = WallexResilientPipeline(max_retries=2, backoff_factor=0.01)
    mock_order_api = Mock(side_effect=TimeoutError("Network dropped during submit"))

    # 1. Order submission times out
    res = pipeline.submit_resilient_order(
        client_order_id="CID_102",
        symbol="ETHIRT",
        side="BUY",
        price=300000000.0,
        quantity=0.05,
        exchange_order_func=mock_order_api
    )

    assert res["status"] == "UNCONFIRMED_PENDING_RECONCILIATION"
    assert pipeline.reconciler.has_pending_reconciliations() is True

    # 2. Next cycle, query exchange open orders to reconcile
    mock_fetch_open = Mock(return_value=[
        {
            "id": 99442,
            "client_order_id": "CID_102",
            "symbol": "ETHIRT",
            "side": "BUY",
            "price": 300000000.0,
            "quantity": 0.05
        }
    ])

    reconciled = pipeline.run_reconciliation_cycle(fetch_open_orders_func=mock_fetch_open)

    assert "CID_102" in reconciled
    assert reconciled["CID_102"]["status"] == "OPEN_ON_EXCHANGE"
    assert pipeline.reconciler.has_pending_reconciliations() is False
