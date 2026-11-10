from typing import Dict, Any, List

class WallexOrderBookLiquidityGuard:
    """
    Evaluates real-time Wallex orderbook depth and checks whether order execution
    will exceed allowable slippage thresholds.
    """
    def __init__(self, max_slippage_pct: float = 0.005, min_depth_coverage_ratio: float = 1.2):
        self.max_slippage_pct = max_slippage_pct
        self.min_depth_coverage_ratio = min_depth_coverage_ratio

    def evaluate_execution_slippage(
        self,
        side: str,
        target_qty: float,
        orderbook: Dict[str, List[List[float]]]
    ) -> Dict[str, Any]:
        """
        orderbook format: {'bids': [[price, qty], ...], 'asks': [[price, qty], ...]}
        side: 'BUY' (scans asks) or 'SELL' (scans bids)
        """
        normalized_side = side.upper()
        levels = orderbook.get("asks" if normalized_side == "BUY" else "bids", [])

        if not levels or target_qty <= 0:
            return {
                "allowed": False,
                "reason": "EMPTY_ORDERBOOK_OR_INVALID_QTY",
                "estimated_vwap": 0.0,
                "slippage_pct": 0.0
            }

        best_price = float(levels[0][0])
        total_depth_qty = sum(float(lvl[1]) for lvl in levels)

        if total_depth_qty < (target_qty * self.min_depth_coverage_ratio):
            return {
                "allowed": False,
                "reason": "INSUFFICIENT_LIQUIDITY_DEPTH",
                "estimated_vwap": 0.0,
                "slippage_pct": 0.0,
                "available_depth": total_depth_qty,
                "required_depth": target_qty * self.min_depth_coverage_ratio
            }

        accumulated_qty = 0.0
        accumulated_cost = 0.0

        for price_val, qty_val in levels:
            p = float(price_val)
            q = float(qty_val)
            remaining = target_qty - accumulated_qty
            if q >= remaining:
                accumulated_cost += remaining * p
                accumulated_qty += remaining
                break
            else:
                accumulated_cost += q * p
                accumulated_qty += q

        vwap = accumulated_cost / accumulated_qty if accumulated_qty > 0 else best_price
        
        if normalized_side == "BUY":
            slippage_pct = (vwap - best_price) / best_price
        else:
            slippage_pct = (best_price - vwap) / best_price

        if slippage_pct > self.max_slippage_pct:
            return {
                "allowed": False,
                "reason": "EXCESSIVE_SLIPPAGE",
                "estimated_vwap": round(vwap, 4),
                "slippage_pct": round(slippage_pct, 6),
                "max_allowed_pct": self.max_slippage_pct
            }

        return {
            "allowed": True,
            "reason": "APPROVED",
            "estimated_vwap": round(vwap, 4),
            "slippage_pct": round(slippage_pct, 6),
            "best_price": best_price
        }
