import pytest
import time
from src.core.order_state_reconciler import OrderStateReconciler

def test_reconcile_open_order():
    reconciler = OrderStateReconciler()
    cid = "cid_order_101"
    
    reconciler.register_unconfirmed_submission(
        client_order_id=cid,
        symbol="BTCIRT",
        side="BUY",
        price=6000000000.0,
        quantity=0.005,
        timestamp=time.time()
    )
    assert reconciler.has_pending_reconciliations() is True

    # Simulate exchange open orders returned
    exchange_orders = [
        {
            "id": 998811,
            "client_order_id": "cid_order_101",
            "symbol": "BTCIRT",
            "side": "BUY",
            "price": 6000000000.0,
            "quantity": 0.005
        }
    ]

    reconciled = reconciler.reconcile_with_exchange(exchange_orders)
    assert cid in reconciled
    assert reconciled[cid]["status"] == "OPEN_ON_EXCHANGE"
    assert reconciled[cid]["exchange_order_id"] == 998811
    assert reconciler.has_pending_reconciliations() is False

def test_reconcile_instantly_filled_order():
    reconciler = OrderStateReconciler()
    cid = "cid_order_102"

    reconciler.register_unconfirmed_submission(
        client_order_id=cid,
        symbol="ETHIRT",
        side="SELL",
        price=300000000.0,
        quantity=0.1,
        timestamp=time.time()
    )

    # Empty open orders, but exists in recent trades
    exchange_orders = []
    exchange_trades = [
        {
            "id": 776655,
            "order_id": 554433,
            "client_order_id": "cid_order_102",
            "symbol": "ETHIRT",
            "side": "SELL",
            "price": 300000000.0,
            "quantity": 0.1
        }
    ]

    reconciled = reconciler.reconcile_with_exchange(exchange_orders, exchange_trades)
    assert cid in reconciled
    assert reconciled[cid]["status"] == "FILLED_ON_EXCHANGE"
    assert reconciled[cid]["exchange_order_id"] == 554433
    assert reconciler.has_pending_reconciliations() is False
