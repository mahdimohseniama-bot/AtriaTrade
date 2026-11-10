from typing import Dict, Any, List

class WallexOrderBookLiquidityGuard:
    def __init__(self, *args, **kwargs):
        self.max_allowed_slippage_pct = kwargs.get("max_allowed_slippage_pct", kwargs.get("max_slippage_pct", 0.01))
        self.min_depth_coverage_ratio = kwargs.get("min_depth_coverage_ratio", kwargs.get("min_depth_factor", 1.2))

    def evaluate_execution_slippage(self, side: str, target_volume: float, orderbook: Dict[str, List[List[float]]]) -> Dict[str, Any]:
        side_norm = side.upper()
        book_key = "asks" if side_norm == "BUY" else "bids"
        levels = orderbook.get(book_key, [])

        if not levels or target_volume <= 0:
            return {
                "allowed": False,
                "acceptable": False,
                "reason": "EMPTY_ORDERBOOK_OR_INVALID_QTY",
                "slippage": 1.0,
                "slippage_pct": 1.0,
                "vwap": 0.0,
                "estimated_vwap": 0.0
            }

        total_depth = sum(level[1] for level in levels)
        if total_depth < target_volume * self.min_depth_coverage_ratio:
            return {
                "allowed": False,
                "acceptable": False,
                "reason": "INSUFFICIENT_LIQUIDITY_DEPTH",
                "slippage": 1.0,
                "slippage_pct": 1.0,
                "vwap": 0.0,
                "estimated_vwap": 0.0,
                "available_depth": total_depth
            }

        remaining = target_volume
        cost = 0.0
        best_price = levels[0][0]

        for price, volume in levels:
            fill = min(remaining, volume)
            cost += fill * price
            remaining -= fill
            if remaining <= 0:
                break

        vwap = cost / target_volume
        if side_norm == "BUY":
            slippage = (vwap - best_price) / best_price
        else:
            slippage = (best_price - vwap) / best_price

        allowed = slippage <= self.max_allowed_slippage_pct
        return {
            "allowed": allowed,
            "acceptable": allowed,
            "slippage": slippage,
            "slippage_pct": slippage,
            "vwap": vwap,
            "estimated_vwap": vwap,
            "best_price": best_price,
            "reason": "APPROVED" if allowed else "EXCESSIVE_SLIPPAGE"
        }

    def evaluate_liquidity(self, orderbook: Dict[str, Any], side: str, required_amount: float, reference_price: float) -> Dict[str, Any]:
        res = self.evaluate_execution_slippage(side, required_amount, orderbook)
        return {
            "permitted": res["allowed"],
            "allowed": res["allowed"],
            "slippage": res["slippage"],
            "slippage_pct": res["slippage_pct"],
            "estimated_vwap": res.get("estimated_vwap", res.get("vwap", 0.0)),
            "reason": res.get("reason", "OK")
        }
