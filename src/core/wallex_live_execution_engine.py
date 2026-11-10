from typing import Dict, Any

class WallexLiveExecutionEngine:
    """
    Live order execution engine for Wallex, integrating the safety coordinator,
    position sizer, and exchange adapter.
    """
    def __init__(self, adapter, coordinator, position_sizer):
        self.adapter = adapter
        self.coordinator = coordinator
        self.position_sizer = position_sizer

    def execute_live_order(
        self,
        symbol: str,
        side: str,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        orderbook: Dict[str, Any],
        reference_price: float
    ) -> Dict[str, Any]:
        # 1. Compute safe position size
        size_res = self.position_sizer.compute_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            side=side
        )

        if not size_res.get("allowed", False):
            return {
                "status": "REJECTED",
                "stage": "POSITION_SIZER",
                "reason": size_res.get("reason", "SIZE_CALCULATION_FAILED"),
                "details": size_res
            }

        target_size = size_res["size"]

        # 2. Safety evaluation across supervisor, tolerance, and liquidity guards
        coord_res = self.coordinator.evaluate_pre_trade_safety(
            orderbook=orderbook,
            side=side,
            required_amount=target_size,
            reference_price=reference_price
        )

        if not coord_res.get("allowed", False):
            return {
                "status": "REJECTED",
                "stage": "SAFETY_COORDINATOR",
                "reason": coord_res.get("reason", "SAFETY_CHECK_FAILED"),
                "details": coord_res
            }

        # 3. Dispatch order via adapter
        effective_price = coord_res.get("effective_price", entry_price)
        order_res = self.adapter.create_order(
            symbol=symbol,
            side=side,
            price=effective_price,
            quantity=target_size
        )

        return {
            "status": "EXECUTED",
            "symbol": symbol,
            "side": side,
            "quantity": target_size,
            "price": effective_price,
            "exchange_response": order_res
        }
