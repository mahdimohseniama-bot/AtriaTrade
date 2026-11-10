import time
from typing import Dict, Any, List, Optional

class WallexLiveStateSynchronizer:
    """
    Synchronizes local in-memory active orders and balances with live exchange state,
    handling recovery after network disconnects or restarts.
    """
    def __init__(self, exchange_adapter, max_order_age_sec: float = 300.0):
        self.exchange = exchange_adapter
        self.max_order_age_sec = max_order_age_sec
        self.last_sync_ts: Optional[float] = None
        self.synchronized_orders: Dict[str, Any] = {}
        self.synchronized_balances: Dict[str, float] = {}

    def perform_sync(self, current_ts: Optional[float] = None) -> Dict[str, Any]:
        now = current_ts if current_ts is not None else time.time()
        
        # 1. Fetch raw balances and open orders from exchange
        raw_balances = self.exchange.get_balances()
        raw_open_orders = self.exchange.get_open_orders()

        self.synchronized_balances = {
            asset: float(data.get("available", 0.0)) + float(data.get("locked", 0.0))
            if isinstance(data, dict) else float(data)
            for asset, data in raw_balances.items()
        }

        stale_order_ids = []
        valid_orders = {}

        for order in raw_open_orders:
            order_id = str(order.get("id"))
            created_at = float(order.get("timestamp", now))
            age = now - created_at

            if age > self.max_order_age_sec:
                stale_order_ids.append(order_id)
            else:
                valid_orders[order_id] = order

        self.synchronized_orders = valid_orders
        self.last_sync_ts = now

        return {
            "status": "SYNCED",
            "timestamp": now,
            "balances": self.synchronized_balances,
            "active_orders_count": len(valid_orders),
            "stale_orders": stale_order_ids
        }

    def cancel_stale_orders(self, stale_order_ids: List[str]) -> List[str]:
        cancelled = []
        for oid in stale_order_ids:
            try:
                res = self.exchange.cancel_order(oid)
                if res.get("success", True):
                    cancelled.append(oid)
            except Exception:
                continue
        return cancelled
