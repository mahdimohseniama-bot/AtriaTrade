import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("OrderStateReconciler")

class OrderStateReconciler:
    def __init__(self):
        # Local registry of pending unverified orders: client_order_id -> metadata
        self.pending_reconciliations: Dict[str, Dict[str, Any]] = {}

    def register_unconfirmed_submission(
        self,
        client_order_id: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        timestamp: float
    ) -> None:
        """Tracks an order whose network response was lost/timed out."""
        self.pending_reconciliations[client_order_id] = {
            "symbol": symbol,
            "side": side.upper(),
            "price": float(price),
            "quantity": float(quantity),
            "timestamp": timestamp,
            "resolved": False,
            "status": "UNRESOLVED"
        }

    def reconcile_with_exchange(
        self,
        exchange_open_orders: List[Dict[str, Any]],
        exchange_recent_trades: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Matches pending unconfirmed submissions against live exchange data.
        Returns reconciled results summary.
        """
        reconciled_orders = {}
        recent_trades = exchange_recent_trades or []

        for cid, info in list(self.pending_reconciliations.items()):
            if info["resolved"]:
                continue

            matched = False
            # 1. Check open orders
            for eo in exchange_open_orders:
                # Match by client_order_id or symbol + side + price + qty
                eo_cid = str(eo.get("client_order_id", ""))
                if (eo_cid and eo_cid == cid) or (
                    eo.get("symbol") == info["symbol"]
                    and eo.get("side", "").upper() == info["side"]
                    and abs(float(eo.get("price", 0)) - info["price"]) < 1e-6
                    and abs(float(eo.get("quantity", 0)) - info["quantity"]) < 1e-6
                ):
                    info["resolved"] = True
                    info["status"] = "OPEN_ON_EXCHANGE"
                    info["exchange_order_id"] = eo.get("id") or eo.get("order_id")
                    reconciled_orders[cid] = info
                    matched = True
                    break

            if matched:
                continue

            # 2. Check recent trades if not open (it might have been filled immediately)
            for trade in recent_trades:
                trade_cid = str(trade.get("client_order_id", ""))
                if (trade_cid and trade_cid == cid) or (
                    trade.get("symbol") == info["symbol"]
                    and trade.get("side", "").upper() == info["side"]
                    and abs(float(trade.get("price", 0)) - info["price"]) < 1e-6
                    and abs(float(trade.get("quantity", 0)) - info["quantity"]) < 1e-6
                ):
                    info["resolved"] = True
                    info["status"] = "FILLED_ON_EXCHANGE"
                    info["exchange_order_id"] = trade.get("order_id") or trade.get("id")
                    reconciled_orders[cid] = info
                    matched = True
                    break

        return reconciled_orders

    def has_pending_reconciliations(self) -> bool:
        return any(not info["resolved"] for info in self.pending_reconciliations.values())

    def clear_resolved(self) -> None:
        self.pending_reconciliations = {
            cid: info for cid, info in self.pending_reconciliations.items()
            if not info["resolved"]
        }
