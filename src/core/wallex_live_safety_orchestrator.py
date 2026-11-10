import logging
from typing import Dict, Any, Optional
from src.core.live_execution_manager import LiveExecutionManager
from src.core.live_position_reconciler import LivePositionReconciler
from src.core.live_capital_guardrail import LiveCapitalGuardrail
from src.core.live_circuit_breaker_emergency_manager import LiveCircuitBreakerEmergencyManager

logger = logging.getLogger("WallexLiveSafetyOrchestrator")

class WallexLiveSafetyOrchestrator:
    def __init__(
        self,
        execution_manager: LiveExecutionManager,
        reconciler: LivePositionReconciler,
        guardrail: LiveCapitalGuardrail,
        emergency_manager: LiveCircuitBreakerEmergencyManager
    ):
        self.exec_mgr = execution_manager
        self.reconciler = reconciler
        self.guardrail = guardrail
        self.emergency_mgr = emergency_manager

    def pre_flight_order_check(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        client_order_id: str,
        total_balance: float,
        available_balance: float,
        local_positions: Dict[str, float],
        exchange_positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Runs comprehensive safety checks prior to live order dispatch.
        """
        # 1. Circuit breaker / Emergency halt check
        can_trade = self.emergency_mgr.can_trade()
        if not can_trade["permitted"]:
            logger.critical(f"Order rejected: Circuit breaker active. Reason: {can_trade['reason']}")
            return {
                "approved": False,
                "stage": "CIRCUIT_BREAKER",
                "reason": can_trade["reason"]
            }

        # 2. Position reconciliation drift check
        drift_check = self.reconciler.reconcile(local_positions, exchange_positions)
        if drift_check["has_drift"]:
            self.emergency_mgr.record_error("POSITION_DRIFT_DETECTED")
            logger.error("Order rejected: Position drift detected against Wallex balance.")
            return {
                "approved": False,
                "stage": "POSITION_RECONCILER",
                "reason": "POSITION_DRIFT_EXCEEDED",
                "drift_details": drift_check["drifts"]
            }

        # 3. Capital allocation & reserve floor check
        cap_check = self.guardrail.validate_capital_allocation(
            total_balance=total_balance,
            available_balance=available_balance,
            order_price=price,
            order_quantity=quantity
        )
        if not cap_check["permitted"]:
            logger.warning(f"Order rejected: Capital guardrail tripped. Reason: {cap_check['reason']}")
            return {
                "approved": False,
                "stage": "CAPITAL_GUARDRAIL",
                "reason": cap_check["reason"]
            }

        logger.info(f"Live safety pre-flight passed for order {client_order_id}.")
        return {
            "approved": True,
            "stage": "PASSED",
            "notional": price * quantity
        }
