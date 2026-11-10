import time
import logging
from typing import Dict, Any, List, Optional
from src.core.network_health_monitor import NetworkHealthMonitor
from src.adapters.wallex_resilient_session import WallexResilientSession
from src.core.order_state_reconciler import OrderStateReconciler

logger = logging.getLogger("WallexResilientPipeline")

class WallexResilientPipeline:
    def __init__(
        self,
        network_monitor: Optional[NetworkHealthMonitor] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.1
    ):
        self.monitor = network_monitor or NetworkHealthMonitor()
        self.session = WallexResilientSession(
            network_monitor=self.monitor,
            max_retries=max_retries,
            backoff_factor=backoff_factor
        )
        self.reconciler = OrderStateReconciler()

    def submit_resilient_order(
        self,
        client_order_id: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        exchange_order_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Submits an order through resilient session. If network drops or fails,
        registers order into reconciler for recovery.
        """
        if not self.monitor.is_operation_permitted():
            logger.warning("Submission blocked by circuit breaker: unstable network.")
            return {
                "status": "BLOCKED_CIRCUIT_OPEN",
                "client_order_id": client_order_id,
                "data": None
            }

        res = self.session.request_with_retry(
            f"order_{client_order_id}",
            exchange_order_func,
            *args,
            **kwargs
        )

        if res["success"]:
            return {
                "status": "SUBMITTED",
                "client_order_id": client_order_id,
                "data": res["data"]
            }

        # If network failed, register for reconciliation
        self.reconciler.register_unconfirmed_submission(
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=time.time()
        )
        return {
            "status": "UNCONFIRMED_PENDING_RECONCILIATION",
            "client_order_id": client_order_id,
            "error": res["error"]
        }

    def run_reconciliation_cycle(
        self,
        fetch_open_orders_func,
        fetch_trades_func=None
    ) -> Dict[str, Any]:
        """Queries exchange to reconcile unconfirmed pending orders."""
        if not self.reconciler.has_pending_reconciliations():
            return {}

        open_res = self.session.request_with_retry("fetch_open_orders", fetch_open_orders_func)
        trades_res = None
        if fetch_trades_func:
            trades_res = self.session.request_with_retry("fetch_trades", fetch_trades_func)

        open_orders = open_res["data"] if open_res["success"] and open_res["data"] else []
        trades = trades_res["data"] if trades_res and trades_res["success"] and trades_res["data"] else []

        reconciled = self.reconciler.reconcile_with_exchange(open_orders, trades)
        self.reconciler.clear_resolved()
        return reconciled
