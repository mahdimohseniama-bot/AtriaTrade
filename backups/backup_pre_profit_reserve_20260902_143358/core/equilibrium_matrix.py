"""
SMC Equilibrium & Premium/Discount Matrix (Capability 89)
Determines market dealing ranges, Equilibrium (50%), Premium, and Discount zones,
and enforces institutional trade direction filters.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ZoneEvaluation:
    current_price: float
    range_high: float
    range_low: float
    equilibrium: float
    relative_position_pct: float  # 0.0 (Low) to 1.0 (High)
    zone: str                     # "DEEP_DISCOUNT", "DISCOUNT", "EQUILIBRIUM", "PREMIUM", "EXTREME_PREMIUM"
    long_allowed: bool
    short_allowed: bool
    reason: str

class EquilibriumMatrix:
    def __init__(self, eq_buffer_pct: float = 0.02):
        """
        :param eq_buffer_pct: Neutral buffer around 50% Equilibrium (e.g. 0.49 to 0.51)
        """
        self.eq_buffer_pct = eq_buffer_pct

    def evaluate_zone(self, current_price: float, range_high: float, range_low: float) -> ZoneEvaluation:
        """
        Evaluates current price relative to dealing range (range_high, range_low).
        """
        if range_high <= range_low or range_low <= 0 or current_price <= 0:
            return ZoneEvaluation(
                current_price=current_price,
                range_high=range_high,
                range_low=range_low,
                equilibrium=0.0,
                relative_position_pct=0.0,
                zone="INVALID",
                long_allowed=False,
                short_allowed=False,
                reason="Invalid range boundaries or negative price"
            )

        range_span = range_high - range_low
        eq = range_low + (range_span * 0.5)
        rel_pos = (current_price - range_low) / range_span

        # Boundary checks
        if current_price > range_high:
            return ZoneEvaluation(
                current_price=current_price,
                range_high=range_high,
                range_low=range_low,
                equilibrium=eq,
                relative_position_pct=rel_pos,
                zone="EXTREME_PREMIUM",
                long_allowed=False,
                short_allowed=True,
                reason="Price expanded above range high into extreme premium"
            )
        
        if current_price < range_low:
            return ZoneEvaluation(
                current_price=current_price,
                range_high=range_high,
                range_low=range_low,
                equilibrium=eq,
                relative_position_pct=rel_pos,
                zone="DEEP_DISCOUNT",
                long_allowed=True,
                short_allowed=False,
                reason="Price expanded below range low into deep discount"
            )

        # Classification based on percentage within range
        if 0.5 - self.eq_buffer_pct <= rel_pos <= 0.5 + self.eq_buffer_pct:
            zone = "EQUILIBRIUM"
            long_allowed = True
            short_allowed = True
            reason = "Price at equilibrium (fair value)"
        elif rel_pos > 0.75:
            zone = "EXTREME_PREMIUM"
            long_allowed = False
            short_allowed = True
            reason = "Price in extreme premium zone (> 75% of range)"
        elif rel_pos > 0.5 + self.eq_buffer_pct:
            zone = "PREMIUM"
            long_allowed = False
            short_allowed = True
            reason = "Price in premium zone (> Equilibrium)"
        elif rel_pos < 0.25:
            zone = "DEEP_DISCOUNT"
            long_allowed = True
            short_allowed = False
            reason = "Price in deep discount zone (< 25% of range)"
        else:
            zone = "DISCOUNT"
            long_allowed = True
            short_allowed = False
            reason = "Price in discount zone (< Equilibrium)"

        return ZoneEvaluation(
            current_price=current_price,
            range_high=range_high,
            range_low=range_low,
            equilibrium=eq,
            relative_position_pct=rel_pos,
            zone=zone,
            long_allowed=long_allowed,
            short_allowed=short_allowed,
            reason=reason
        )

    def validate_signal_direction(self, signal_type: str, current_price: float, range_high: float, range_low: float) -> Dict[str, Any]:
        """
        Filters incoming signals to prevent buying in Premium or selling in Discount.
        """
        eval_res = self.evaluate_zone(current_price, range_high, range_low)
        sig = signal_type.upper()

        if not eval_res.long_allowed and sig in ["BUY", "LONG"]:
            return {
                "valid": False,
                "reason": f"Signal {sig} rejected: Cannot buy in {eval_res.zone} zone",
                "evaluation": eval_res
            }

        if not eval_res.short_allowed and sig in ["SELL", "SHORT"]:
            return {
                "valid": False,
                "reason": f"Signal {sig} rejected: Cannot sell in {eval_res.zone} zone",
                "evaluation": eval_res
            }

        return {
            "valid": True,
            "reason": f"Signal {sig} confirmed in favorable {eval_res.zone} zone",
            "evaluation": eval_res
        }
