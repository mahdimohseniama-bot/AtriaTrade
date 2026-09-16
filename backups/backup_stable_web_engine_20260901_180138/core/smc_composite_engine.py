"""
SMC Institutional Order Flow & Composite Signal Engine (Capability 90)
Aggregates SMC concepts (OB, FVG, OTE, Liquidity, Session Range, Equilibrium)
into a unified, high-probability institutional signal.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.core.equilibrium_matrix import EquilibriumMatrix

@dataclass
class SMCCompositeSignal:
    symbol: str
    direction: str             # "BUY", "SELL", "NEUTRAL"
    confidence: str            # "HIGH", "MEDIUM", "LOW", "REJECTED"
    score: float               # 0.0 to 100.0
    entry_price: float
    stop_loss: float
    take_profit: float
    confluences: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None

class SMCCompositeEngine:
    def __init__(self, min_confidence_score: float = 60.0):
        self.min_confidence_score = min_confidence_score
        self.eq_matrix = EquilibriumMatrix()

    def generate_signal(
        self,
        symbol: str,
        current_price: float,
        range_high: float,
        range_low: float,
        fvg_detected: bool = False,
        fvg_direction: Optional[str] = None,
        ob_detected: bool = False,
        ob_direction: Optional[str] = None,
        ote_aligned: bool = False,
        liquidity_swept: bool = False,
        breaker_confirmed: bool = False
    ) -> SMCCompositeSignal:
        """
        Evaluates institutional SMC confluences and generates unified trade decision.
        """
        if current_price <= 0 or range_high <= range_low:
            return SMCCompositeSignal(
                symbol=symbol,
                direction="NEUTRAL",
                confidence="REJECTED",
                score=0.0,
                entry_price=current_price,
                stop_loss=0.0,
                take_profit=0.0,
                rejection_reason="Invalid market parameters"
            )

        # 1. Evaluate Equilibrium Zone
        zone_eval = self.eq_matrix.evaluate_zone(current_price, range_high, range_low)
        
        # Base direction bias from zone & primary triggers
        bullish_votes = 0
        bearish_votes = 0
        confluences = []

        if zone_eval.zone in ["DISCOUNT", "DEEP_DISCOUNT"]:
            bullish_votes += 25
            confluences.append(f"Price in favorable {zone_eval.zone}")
        elif zone_eval.zone in ["PREMIUM", "EXTREME_PREMIUM"]:
            bearish_votes += 25
            confluences.append(f"Price in favorable {zone_eval.zone}")

        if fvg_detected and fvg_direction:
            if fvg_direction.upper() in ["BUY", "BULLISH"]:
                bullish_votes += 20
                confluences.append("Bullish FVG support")
            elif fvg_direction.upper() in ["SELL", "BEARISH"]:
                bearish_votes += 20
                confluences.append("Bearish FVG resistance")

        if ob_detected and ob_direction:
            if ob_direction.upper() in ["BULLISH", "BUY"]:
                bullish_votes += 25
                confluences.append("Bullish Order Block mitigation")
            elif ob_direction.upper() in ["BEARISH", "SELL"]:
                bearish_votes += 25
                confluences.append("Bearish Order Block supply")

        if ote_aligned:
            confluences.append("OTE (0.618 - 0.786) retracement level aligned")
            bullish_votes += 15
            bearish_votes += 15

        if liquidity_swept:
            confluences.append("Session / Key Liquidity Sweep completed")
            bullish_votes += 15
            bearish_votes += 15

        if breaker_confirmed:
            confluences.append("Breaker/Mitigation Block confirmation")
            bullish_votes += 10
            bearish_votes += 10

        # Determine winner
        if bullish_votes > bearish_votes and zone_eval.long_allowed:
            final_dir = "BUY"
            final_score = min(100.0, float(bullish_votes))
            sl = range_low * 0.998  # Just below range low
            tp = range_high         # Target range high
        elif bearish_votes > bullish_votes and zone_eval.short_allowed:
            final_dir = "SELL"
            final_score = min(100.0, float(bearish_votes))
            sl = range_high * 1.002 # Just above range high
            tp = range_low          # Target range low
        else:
            return SMCCompositeSignal(
                symbol=symbol,
                direction="NEUTRAL",
                confidence="REJECTED",
                score=0.0,
                entry_price=current_price,
                stop_loss=0.0,
                take_profit=0.0,
                confluences=confluences,
                rejection_reason="Contradictory directional bias or zone constraint"
            )

        if final_score < self.min_confidence_score:
            confidence = "LOW"
        elif final_score >= 80.0:
            confidence = "HIGH"
        else:
            confidence = "MEDIUM"

        return SMCCompositeSignal(
            symbol=symbol,
            direction=final_dir,
            confidence=confidence,
            score=final_score,
            entry_price=current_price,
            stop_loss=round(sl, 4),
            take_profit=round(tp, 4),
            confluences=confluences,
            rejection_reason=None
        )
