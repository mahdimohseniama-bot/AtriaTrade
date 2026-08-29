"""
Profit Locker and Peak Profit Protector for AtriaTrade (Capability 78).
Protects unrealized gains by establishing dynamic profit floor barriers.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PositionProfitTracker:
    position_id: str
    entry_price: float
    size: float
    direction: str  # "BUY" or "SELL"
    peak_pnl: float = 0.0
    current_pnl: float = 0.0
    locked_profit_floor: float = 0.0
    tier1_threshold: float = 100.0   # Trigger at $100 profit
    tier1_lock_ratio: float = 0.50   # Lock 50% ($50)
    tier2_threshold: float = 200.0   # Trigger at $200 profit
    tier2_lock_ratio: float = 0.75   # Lock 75% ($150)


class ProfitLocker:
    def __init__(self):
        pass

    def evaluate_price(
        self,
        tracker: PositionProfitTracker,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Updates current PnL, adjusts profit floors, and checks if position should be closed to protect profit.
        """
        is_buy = tracker.direction.upper() == "BUY"
        
        # Calculate current unrealized PnL
        if is_buy:
            pnl = (current_price - tracker.entry_price) * tracker.size
        else:
            pnl = (tracker.entry_price - current_price) * tracker.size

        tracker.current_pnl = round(pnl, 4)

        # Update peak PnL
        if tracker.current_pnl > tracker.peak_pnl:
            tracker.peak_pnl = tracker.current_pnl

        # Calculate dynamic profit floor based on peak
        if tracker.peak_pnl >= tracker.tier2_threshold:
            floor = tracker.peak_pnl * tracker.tier2_lock_ratio
            if floor > tracker.locked_profit_floor:
                tracker.locked_profit_floor = round(floor, 4)
        elif tracker.peak_pnl >= tracker.tier1_threshold:
            floor = tracker.peak_pnl * tracker.tier1_lock_ratio
            if floor > tracker.locked_profit_floor:
                tracker.locked_profit_floor = round(floor, 4)

        # Check breach of locked floor
        should_close = False
        reason = "NORMAL"

        if tracker.locked_profit_floor > 0 and tracker.current_pnl < tracker.locked_profit_floor:
            should_close = True
            reason = "PROFIT_PROTECTION_TRIGGERED"

        return {
            "position_id": tracker.position_id,
            "current_price": current_price,
            "current_pnl": tracker.current_pnl,
            "peak_pnl": tracker.peak_pnl,
            "locked_profit_floor": tracker.locked_profit_floor,
            "should_close": should_close,
            "reason": reason
        }
