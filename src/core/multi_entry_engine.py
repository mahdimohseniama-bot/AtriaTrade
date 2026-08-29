"""
Smart Multi-Entry and Position Scaling Engine for AtriaTrade (Capability 75).
Handles institutional tiered entries, volume-weighted average price calculation, and scale-in risk management.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EntryTier:
    tier_number: int
    entry_price: float
    size: float
    reason: str


@dataclass
class MultiEntryPosition:
    symbol: str
    direction: str  # "BUY" or "SELL"
    total_size: float = 0.0
    weighted_avg_price: float = 0.0
    tiers: List[EntryTier] = field(default_factory=list)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class MultiEntryEngine:
    def __init__(self, max_tiers: int = 3, max_total_size: float = 10.0):
        if max_tiers <= 0:
            raise ValueError("max_tiers must be greater than 0")
        if max_total_size <= 0.0:
            raise ValueError("max_total_size must be greater than 0")
        self.max_tiers = max_tiers
        self.max_total_size = max_total_size

    def add_tier(
        self,
        position: MultiEntryPosition,
        entry_price: float,
        size: float,
        reason: str = "TIER_ENTRY"
    ) -> MultiEntryPosition:
        if entry_price <= 0.0 or size <= 0.0:
            raise ValueError("Price and size must be positive values")

        if len(position.tiers) >= self.max_tiers:
            raise ValueError(f"Cannot exceed maximum allowed tiers of {self.max_tiers}")

        if position.total_size + size > self.max_total_size:
            raise ValueError(f"Total position size would exceed limit of {self.max_total_size}")

        current_total_cost = position.weighted_avg_price * position.total_size
        new_total_size = position.total_size + size
        new_cost = entry_price * size
        new_weighted_avg = (current_total_cost + new_cost) / new_total_size

        new_tier = EntryTier(
            tier_number=len(position.tiers) + 1,
            entry_price=entry_price,
            size=size,
            reason=reason
        )

        position.tiers.append(new_tier)
        position.total_size = round(new_total_size, 6)
        position.weighted_avg_price = round(new_weighted_avg, 6)

        return position

    def calculate_unrealized_pnl(self, position: MultiEntryPosition, current_price: float) -> float:
        if position.total_size == 0.0 or position.weighted_avg_price == 0.0:
            return 0.0

        if position.direction.upper() == "BUY":
            pnl = (current_price - position.weighted_avg_price) * position.total_size
        else:
            pnl = (position.weighted_avg_price - current_price) * position.total_size

        return round(pnl, 4)
