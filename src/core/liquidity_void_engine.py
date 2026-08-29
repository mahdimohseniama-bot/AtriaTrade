"""
Liquidity Void & Imbalance Rebalancing Engine (Capability 91)
Tracks extreme price displacement gaps (Liquidity Voids), calculates rebalancing fill percentages,
and determines optimal institutional magnet targets.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class LiquidityVoid:
    void_id: str
    symbol: str
    direction: str  # BULLISH_DISPLACEMENT (void below) or BEARISH_DISPLACEMENT (void above)
    top_price: float
    bottom_price: float
    equilibrium_level: float
    filled_ratio: float = 0.0
    status: str = "OPEN"  # OPEN, PARTIALLY_FILLED, FULLY_FILLED

class LiquidityVoidEngine:
    def __init__(self, min_void_pct: float = 0.5):
        """
        :param min_void_pct: Minimum price range % to qualify as an institutional liquidity void
        """
        self.min_void_pct = min_void_pct
        self.voids: List[LiquidityVoid] = []

    def detect_void(
        self,
        symbol: str,
        candle_high: float,
        candle_low: float,
        next_candle_low: Optional[float] = None,
        next_candle_high: Optional[float] = None,
        candle_direction: str = "BULLISH"
    ) -> Optional[LiquidityVoid]:
        """
        Detects sudden expansion displacement leaving open void.
        """
        if candle_high <= candle_low or candle_low <= 0:
            return None

        candle_range_pct = ((candle_high - candle_low) / candle_low) * 100.0
        if candle_range_pct < self.min_void_pct:
            return None

        # Determine void boundaries
        if candle_direction.upper() == "BULLISH":
            top = candle_high
            bottom = candle_low if next_candle_low is None else min(candle_low, next_candle_low)
            direction = "BULLISH_DISPLACEMENT"
        else:
            top = candle_high if next_candle_high is None else max(candle_high, next_candle_high)
            bottom = candle_low
            direction = "BEARISH_DISPLACEMENT"

        eq = round((top + bottom) / 2.0, 4)
        void_id = f"VOID_{symbol}_{len(self.voids) + 1}"

        void = LiquidityVoid(
            void_id=void_id,
            symbol=symbol,
            direction=direction,
            top_price=round(top, 4),
            bottom_price=round(bottom, 4),
            equilibrium_level=eq,
            filled_ratio=0.0,
            status="OPEN"
        )
        self.voids.append(void)
        return void

    def update_rebalance_status(self, void: LiquidityVoid, current_price: float) -> LiquidityVoid:
        """
        Updates how much of the liquidity void has been filled/rebalanced.
        """
        if void.top_price <= void.bottom_price:
            return void

        total_span = void.top_price - void.bottom_price

        if void.direction == "BULLISH_DISPLACEMENT":
            # Price pulls down into the void from top
            if current_price >= void.top_price:
                fill = 0.0
            elif current_price <= void.bottom_price:
                fill = 1.0
            else:
                fill = (void.top_price - current_price) / total_span
        else:
            # Price pulls up into the void from bottom
            if current_price <= void.bottom_price:
                fill = 0.0
            elif current_price >= void.top_price:
                fill = 1.0
            else:
                fill = (current_price - void.bottom_price) / total_span

        void.filled_ratio = max(0.0, min(1.0, round(fill, 4)))

        if void.filled_ratio >= 1.0:
            void.status = "FULLY_FILLED"
        elif void.filled_ratio >= 0.5:
            void.status = "PARTIALLY_FILLED"
        else:
            void.status = "OPEN"

        return void

    def get_active_targets(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Returns active 50% rebalance and 100% full-fill magnet price targets.
        """
        targets = []
        for v in self.voids:
            if v.symbol == symbol and v.status != "FULLY_FILLED":
                targets.append({
                    "void_id": v.void_id,
                    "direction": v.direction,
                    "equilibrium_50pct": v.equilibrium_level,
                    "full_fill_price": v.bottom_price if v.direction == "BULLISH_DISPLACEMENT" else v.top_price,
                    "filled_ratio": v.filled_ratio,
                    "status": v.status
                })
        return targets
