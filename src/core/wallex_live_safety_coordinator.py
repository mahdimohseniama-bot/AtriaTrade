from typing import Dict, Any, Optional

class WallexLiveSafetyCoordinator:
    """
    Coordinates safety validations, orderbook liquidity checks, and execution
    tolerance prior to dispatching live orders to the Wallex exchange.
    """
    def __init__(self, supervisor, liquidity_guard, tolerance_guard):
        self.supervisor = supervisor
        self.liquidity_guard = liquidity_guard
        self.tolerance_guard = tolerance_guard

    def evaluate_pre_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        signal_price: float,
        current_market_price: float,
        orderbook: Dict[str, Any],
        signal_timestamp: float,
        current_timestamp: float
    ) -> Dict[str, Any]:
        # 1. System Health Check
        health = self.supervisor.check_health(current_timestamp)
        if not health["healthy"]:
            return {
                "permitted": False,
                "stage": "SUPERVISOR",
                "reason": health["reason"]
            }

        # 2. Execution Price Drift Tolerance Check
        tol_res = self.tolerance_guard.validate_execution_price(
            side=side,
            signal_price=signal_price,
            current_market_price=current_market_price,
            signal_timestamp=signal_timestamp,
            current_timestamp=current_timestamp
        )
        if not tol_res["allowed"]:
            return {
                "permitted": False,
                "stage": "TOLERANCE_GUARD",
                "reason": tol_res["reason"],
                "details": tol_res
            }

        # 3. Orderbook Depth & Liquidity Check
        liq_res = self.liquidity_guard.evaluate_liquidity(
            orderbook=orderbook,
            side=side,
            required_amount=amount,
            reference_price=current_market_price
        )
        if not liq_res["allowed"]:
            return {
                "permitted": False,
                "stage": "LIQUIDITY_GUARD",
                "reason": liq_res["reason"],
                "details": liq_res
            }

        return {
            "permitted": True,
            "stage": "APPROVED",
            "reason": "ALL_SAFETY_CHECKS_PASSED",
            "estimated_price": liq_res.get("effective_price", current_market_price),
            "estimated_slippage_pct": liq_res.get("slippage_pct", 0.0),
            "drift_pct": tol_res.get("drift_pct", 0.0)
        }
