from typing import Dict, Any, List

class WallexLiveReconciliationEngine:
    """
    Reconciles live exchange state (account balances, open orders, filled trades)
    with local bot tracking state to prevent drift and out-of-sync executions.
    """
    def __init__(self, adapter, tolerance_threshold: float = 0.0001):
        self.adapter = adapter
        self.tolerance_threshold = tolerance_threshold

    def reconcile_balances(self, local_balance: float, currency: str = "USDT") -> Dict[str, Any]:
        live_balances = self.adapter.get_balances()
        remote_balance = float(live_balances.get(currency, 0.0))

        diff = abs(remote_balance - local_balance)
        is_synced = diff <= self.tolerance_threshold

        return {
            "synced": is_synced,
            "currency": currency,
            "local_balance": local_balance,
            "remote_balance": remote_balance,
            "discrepancy": round(diff, 6),
            "status": "SYNCED" if is_synced else "BALANCE_MISMATCH"
        }

    def reconcile_open_orders(self, local_open_order_ids: List[str], symbol: str = "BTCUSDT") -> Dict[str, Any]:
        remote_open_orders = self.adapter.get_open_orders(symbol=symbol)
        remote_order_ids = [str(o.get("id")) for o in remote_open_orders if "id" in o]

        orphans_local = [oid for oid in local_open_order_ids if oid not in remote_order_ids]
        orphans_remote = [oid for oid in remote_order_ids if oid not in local_open_order_ids]

        is_synced = len(orphans_local) == 0 and len(orphans_remote) == 0

        return {
            "synced": is_synced,
            "local_count": len(local_open_order_ids),
            "remote_count": len(remote_order_ids),
            "local_orphans": orphans_local,
            "remote_orphans": orphans_remote,
            "status": "ORDERS_ALIGNED" if is_synced else "ORDERS_MISMATCH"
        }
