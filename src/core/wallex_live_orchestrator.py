import logging
from typing import Dict, Any, List

logger = logging.getLogger("AtriaTrade.WallexLiveOrchestrator")

class WallexLiveOrchestrator:
    def __init__(
        self,
        execution_engine: Any,
        heartbeat_monitor: Any,
        rate_limiter: Any,
        reconciler: Any
    ):
        self.engine = execution_engine
        self.heartbeat = heartbeat_monitor
        self.limiter = rate_limiter
        self.reconciler = reconciler

    def pre_flight_check(self) -> Dict[str, Any]:
        """
        Validates connectivity and rate limits before attempting trading actions.
        """
        # 1. Rate limiter check
        if not self.limiter.acquire(1.0):
            logger.warning("Pre-flight rejected: rate limit reached")
            return {"ready": False, "reason": "rate_limited"}

        # 2. Heartbeat check
        beat = self.heartbeat.ping()
        if not beat.get("is_healthy", False) or self.heartbeat.should_pause_trading():
            logger.error(f"Pre-flight rejected: heartbeat unhealthy ({beat.get('reason')})")
            return {"ready": False, "reason": "network_unhealthy", "heartbeat": beat}

        return {"ready": True, "reason": "ok", "latency_ms": beat.get("latency_ms", 0.0)}

    def execute_live_cycle(
        self,
        symbol: str,
        signal: Dict[str, Any],
        active_order_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Runs a safe live cycle: pre-flight check -> orphan order reconciliation -> order execution.
        """
        # Step 1: Pre-flight check
        check = self.pre_flight_check()
        if not check["ready"]:
            return {"status": "skipped", "reason": check["reason"]}

        # Step 2: Reconcile open orders
        recon = self.reconciler.reconcile_open_orders(symbol=symbol, internal_order_ids=active_order_ids)
        if recon.get("orphan_orders"):
            logger.warning(f"Detected orphan orders: {recon['orphan_orders']}. Cancelling...")
            self.reconciler.cancel_orphan_orders(symbol=symbol, orphan_ids=recon["orphan_orders"])

        # Step 3: Execute trade if signal is present
        if signal and signal.get("action") in ("BUY", "SELL"):
            exec_res = self.engine.execute_order(
                symbol=symbol,
                side=signal["action"],
                amount=signal.get("amount", 0.0),
                price=signal.get("price", 0.0)
            )
            return {
                "status": "executed",
                "execution": exec_res,
                "reconciliation": recon
            }

        return {"status": "idle", "reconciliation": recon}
