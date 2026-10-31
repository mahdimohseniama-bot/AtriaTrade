import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("AtriaTrade.WallexRecovery")

class RecoveryState(Enum):
    INIT = "INIT"
    SYNCED = "SYNCED"
    RESOLVED_ORPHANS = "RESOLVED_ORPHANS"
    SAFE_MODE = "SAFE_MODE"

@dataclass
class RecoveryReport:
    state: RecoveryState
    is_clean_sync: bool
    balances: Dict[str, float] = field(default_factory=dict)
    open_orders: List[Dict[str, Any]] = field(default_factory=list)
    orphan_order_ids: List[str] = field(default_factory=list)
    orphan_orders_found: int = 0
    cancelled_orphans: int = 0
    error_message: Optional[str] = None

class WallexRecoveryManager:
    """
    Automated State Recovery & Crash Resolver for Wallex Live Operations.
    Safeguards capital across unexpected crashes or network drops.
    """
    def __init__(self, exchange_adapter: Any):
        self.exchange = exchange_adapter

    def recover_and_sync(
        self,
        symbol: str = "BTCUSDT",
        known_internal_orders: Optional[List[str]] = None,
        cancel_orphans: bool = True
    ) -> RecoveryReport:
        known_internal = set(known_internal_orders or [])
        logger.info(f"Starting recovery check for symbol {symbol} with {len(known_internal)} known orders...")

        # Step 1: Health & Connectivity Check via Balance / Order Fetch
        try:
            balances = self.exchange.get_balances()
            exchange_orders = self.exchange.get_open_orders(symbol=symbol)
        except Exception as exc:
            err_msg = str(exc)
            logger.critical(f"Recovery failed due to network/API error: {err_msg}")
            return RecoveryReport(
                state=RecoveryState.SAFE_MODE,
                is_clean_sync=False,
                error_message=err_msg
            )

        # Step 2: Detect Orphan Orders
        live_order_ids = {str(o.get("id")) for o in exchange_orders if o.get("id") is not None}
        orphan_ids = [oid for oid in live_order_ids if oid not in known_internal]
        cancelled_count = 0

        # Step 3: Handle Orphans
        if orphan_ids:
            logger.warning(f"Detected {len(orphan_ids)} orphan orders on exchange: {orphan_ids}")
            if cancel_orphans:
                for oid in orphan_ids:
                    try:
                        self.exchange.cancel_order(order_id=oid)
                        cancelled_count += 1
                        logger.info(f"Cancelled orphan order {oid}")
                    except Exception as cancel_exc:
                        logger.error(f"Failed to cancel orphan order {oid}: {cancel_exc}")

            return RecoveryReport(
                state=RecoveryState.RESOLVED_ORPHANS,
                is_clean_sync=False,
                balances=balances,
                open_orders=exchange_orders,
                orphan_order_ids=orphan_ids,
                orphan_orders_found=len(orphan_ids),
                cancelled_orphans=cancelled_count
            )

        # Step 4: Clean Sync
        logger.info("Exchange state cleanly aligned with internal tracking.")
        return RecoveryReport(
            state=RecoveryState.SYNCED,
            is_clean_sync=True,
            balances=balances,
            open_orders=exchange_orders,
            orphan_orders_found=0,
            cancelled_orphans=0
        )
