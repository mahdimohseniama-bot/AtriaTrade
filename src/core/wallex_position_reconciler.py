import logging
from typing import Dict, Any, List

logger = logging.getLogger("AtriaTrade.WallexPositionReconciler")

class WallexPositionReconciler:
    def __init__(self, exchange_adapter: Any):
        self.adapter = exchange_adapter

    def reconcile_open_orders(self, symbol: str, internal_order_ids: List[str]) -> Dict[str, Any]:
        """
        Reconciles internal tracked orders with active exchange orders.
        Detects orphan orders (open on exchange but not tracked locally).
        """
        try:
            exchange_orders = self.adapter.get_open_orders(symbol=symbol)
            if not isinstance(exchange_orders, list):
                logger.error("Invalid open orders response: expected list")
                return {"status": "error", "reason": "invalid_response", "orphans": []}

            exchange_order_ids = {str(o.get("id") or o.get("order_id")) for o in exchange_orders if isinstance(o, dict)}
            internal_set = set(str(oid) for oid in internal_order_ids)

            orphan_ids = list(exchange_order_ids - internal_set)
            missing_ids = list(internal_set - exchange_order_ids)

            return {
                "status": "synchronized",
                "exchange_count": len(exchange_order_ids),
                "internal_count": len(internal_set),
                "orphan_orders": orphan_ids,
                "missing_on_exchange": missing_ids
            }
        except Exception as e:
            logger.error(f"Error during order reconciliation: {e}")
            return {"status": "error", "reason": str(e), "orphan_orders": [], "missing_on_exchange": []}

    def cancel_orphan_orders(self, symbol: str, orphan_ids: List[str]) -> Dict[str, int]:
        """
        Safely cancels orphan orders on the exchange to prevent unintended fills.
        """
        cancelled_count = 0
        failed_count = 0

        for order_id in orphan_ids:
            try:
                res = self.adapter.cancel_order(symbol=symbol, order_id=order_id)
                if res and res.get("status") in ("success", "cancelled", "ok", True):
                    cancelled_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to cancel orphan order {order_id}: {e}")
                failed_count += 1

        return {"cancelled": cancelled_count, "failed": failed_count}
