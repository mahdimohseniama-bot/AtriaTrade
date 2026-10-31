import time
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("AtriaTrade.WallexSlippageGuard")

@dataclass
class SlippageCheckResult:
    symbol: str
    is_allowed: bool
    estimated_average_price: float
    slippage_pct: float
    rejection_reason: Optional[str] = None

class WallexSlippageGuard:
    """
    Evaluates order book depth and quote latency before dispatching 
    live orders to Wallex, mitigating high slippage and stale execution.
    """

    def __init__(self, max_slippage_pct: float = 0.5, max_latency_sec: float = 3.0):
        self.max_slippage_pct = max_slippage_pct
        self.max_latency_sec = max_latency_sec

    def evaluate_order_execution(
        self,
        symbol: str,
        side: str,
        target_qty: float,
        expected_price: float,
        orderbook_side: List[Tuple[float, float]],
        quote_timestamp: float
    ) -> SlippageCheckResult:
        current_time = time.time()
        latency = current_time - quote_timestamp

        if latency > self.max_latency_sec:
            logger.warning(f"Orderbook stale for {symbol}: latency={latency:.2f}s > {self.max_latency_sec}s")
            return SlippageCheckResult(
                symbol=symbol,
                is_allowed=False,
                estimated_average_price=0.0,
                slippage_pct=0.0,
                rejection_reason="ORDERBOOK_STALE"
            )

        if not orderbook_side or target_qty <= 0:
            return SlippageCheckResult(
                symbol=symbol,
                is_allowed=False,
                estimated_average_price=0.0,
                slippage_pct=0.0,
                rejection_reason="INSUFFICIENT_LIQUIDITY"
            )

        remaining_qty = target_qty
        total_cost = 0.0

        for price, depth_qty in orderbook_side:
            fill_qty = min(remaining_qty, depth_qty)
            total_cost += fill_qty * price
            remaining_qty -= fill_qty
            if remaining_qty <= 1e-9:
                break

        if remaining_qty > 1e-9:
            logger.warning(f"Insufficient orderbook depth to fill {target_qty} of {symbol}")
            return SlippageCheckResult(
                symbol=symbol,
                is_allowed=False,
                estimated_average_price=0.0,
                slippage_pct=0.0,
                rejection_reason="INSUFFICIENT_DEPTH"
            )

        avg_fill_price = total_cost / target_qty

        # Calculate slippage percentage based on order side
        if side.upper() == "BUY":
            slippage_pct = ((avg_fill_price - expected_price) / expected_price) * 100.0
        else:
            slippage_pct = ((expected_price - avg_fill_price) / expected_price) * 100.0

        slippage_pct = max(0.0, slippage_pct)

        if slippage_pct > self.max_slippage_pct:
            logger.warning(f"Slippage {slippage_pct:.3f}% exceeds limit {self.max_slippage_pct}% for {symbol}")
            return SlippageCheckResult(
                symbol=symbol,
                is_allowed=False,
                estimated_average_price=avg_fill_price,
                slippage_pct=slippage_pct,
                rejection_reason="SLIPPAGE_EXCEEDED"
            )

        return SlippageCheckResult(
            symbol=symbol,
            is_allowed=True,
            estimated_average_price=avg_fill_price,
            slippage_pct=slippage_pct,
            rejection_reason=None
        )
