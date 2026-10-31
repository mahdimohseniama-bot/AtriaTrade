import logging
from typing import Dict, Any, Optional
from src.core.wallex_circuit_breaker import WallexCircuitBreaker
from src.core.wallex_order_guard import WallexOrderGuard
from src.exchange.wallex_balance_syncer import WallexBalanceSyncer

logger = logging.getLogger("AtriaTrade.WallexLiveEngine")

class WallexLiveExecutionEngine:
    def __init__(
        self,
        executor: Any,
        balance_syncer: WallexBalanceSyncer,
        circuit_breaker: Optional[WallexCircuitBreaker] = None,
        order_guard: Optional[WallexOrderGuard] = None
    ):
        self.executor = executor
        self.syncer = balance_syncer
        self.circuit_breaker = circuit_breaker or WallexCircuitBreaker()
        self.order_guard = order_guard or WallexOrderGuard()

    def execute_live_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        best_bid: float,
        best_ask: float
    ) -> Dict[str, Any]:
        """Validates all safety constraints and executes live order via Wallex."""
        # 1. Check Circuit Breaker
        if not self.circuit_breaker.can_execute():
            logger.error("Execution blocked: Circuit breaker is tripped.")
            return {"status": "rejected", "reason": "circuit_breaker_active"}

        # 2. Check Order Guard (Spread & Minimum Order Size)
        is_safe, guard_msg = self.order_guard.is_order_safe(
            amount=amount,
            price=price,
            best_bid=best_bid,
            best_ask=best_ask
        )
        if not is_safe:
            logger.warning(f"Execution rejected by OrderGuard: {guard_msg}")
            return {"status": "rejected", "reason": guard_msg}

        # 3. Check Account Balance
        asset_needed = "USDT" if side.upper() == "BUY" else symbol.replace("USDT", "").replace("TMN", "")
        amount_needed = (amount * price) if side.upper() == "BUY" else amount

        has_balance = self.syncer.has_sufficient_balance(asset_needed, amount_needed)
        if not has_balance:
            balance_msg = f"Insufficient balance for {asset_needed}: required {amount_needed}"
            logger.warning(f"Execution rejected: {balance_msg}")
            return {"status": "rejected", "reason": balance_msg}

        # 4. Dispatch Order
        try:
            res = self.executor.place_order(symbol=symbol, side=side, amount=amount, price=price)
            self.circuit_breaker.record_success()
            return {"status": "executed", "order_result": res}
        except Exception as e:
            err_msg = f"Order execution failed: {str(e)}"
            self.circuit_breaker.record_failure(err_msg)
            logger.error(err_msg)
            return {"status": "failed", "reason": str(e)}
