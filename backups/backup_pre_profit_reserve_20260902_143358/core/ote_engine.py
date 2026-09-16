"""
Optimal Trade Entry (OTE) & ICT Fibonacci Level Engine (Capability 94)
Calculates Equilibrium, Premium/Discount zones, OTE levels (0.618, 0.705, 0.786),
and extension profit targets based on swing ranges.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class MarketZone(str, Enum):
    PREMIUM = "PREMIUM"        # Price > 0.5 Equilibrium
    EQUILIBRIUM = "EQUILIBRIUM"  # Price == 0.5
    DISCOUNT = "DISCOUNT"      # Price < 0.5 Equilibrium


class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class OTEProfile:
    swing_high: float
    swing_low: float
    direction: TradeDirection
    equilibrium: float          # 50.0%
    ote_618: float              # 61.8%
    ote_705: float              # 70.5% (Sweet spot)
    ote_786: float              # 78.6%
    target_ext_27: float        # -27.0% Extension
    target_ext_62: float        # -62.0% Extension


class OTEEngine:
    """
    Computes ICT Optimal Trade Entry levels and evaluates current price zone.
    """

    def __init__(self, sweet_spot: float = 0.705):
        self.sweet_spot = sweet_spot

    def calculate_ote(self, swing_low: float, swing_high: float, direction: TradeDirection) -> OTEProfile:
        """
        Calculates OTE levels based on swing extremes and trade direction.
        """
        if swing_high <= swing_low:
            raise ValueError("swing_high must be strictly greater than swing_low")

        diff = swing_high - swing_low
        eq = swing_low + 0.5 * diff

        if direction == TradeDirection.LONG:
            # Retracement down from high into discount OTE
            ote_618 = swing_high - (0.618 * diff)
            ote_705 = swing_high - (self.sweet_spot * diff)
            ote_786 = swing_high - (0.786 * diff)
            ext_27 = swing_high + (0.27 * diff)
            ext_62 = swing_high + (0.62 * diff)
        else:
            # Retracement up from low into premium OTE
            ote_618 = swing_low + (0.618 * diff)
            ote_705 = swing_low + (self.sweet_spot * diff)
            ote_786 = swing_low + (0.786 * diff)
            ext_27 = swing_low - (0.27 * diff)
            ext_62 = swing_low - (0.62 * diff)

        return OTEProfile(
            swing_high=float(swing_high),
            swing_low=float(swing_low),
            direction=direction,
            equilibrium=round(eq, 6),
            ote_618=round(ote_618, 6),
            ote_705=round(ote_705, 6),
            ote_786=round(ote_786, 6),
            target_ext_27=round(ext_27, 6),
            target_ext_62=round(ext_62, 6),
        )

    def get_market_zone(self, price: float, swing_low: float, swing_high: float) -> MarketZone:
        """
        Identifies whether current price is in Premium or Discount zone.
        """
        if swing_high <= swing_low:
            raise ValueError("swing_high must be strictly greater than swing_low")

        eq = (swing_high + swing_low) / 2.0
        if price > eq:
            return MarketZone.PREMIUM
        elif price < eq:
            return MarketZone.DISCOUNT
        return MarketZone.EQUILIBRIUM

    def is_in_ote_zone(self, price: float, profile: OTEProfile) -> bool:
        """
        Checks if the current price falls inside the OTE range [0.618 to 0.786].
        """
        low_bound = min(profile.ote_618, profile.ote_786)
        high_bound = max(profile.ote_618, profile.ote_786)
        return low_bound <= price <= high_bound
