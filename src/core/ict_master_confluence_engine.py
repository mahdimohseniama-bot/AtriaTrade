from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class SetupGrade(str, Enum):
    A_PLUS = "A_PLUS"   # Confluence score >= 80
    B = "B"            # Confluence score 60 - 79
    C = "C"            # Confluence score 40 - 59
    INVALID = "INVALID" # Confluence score < 40


@dataclass
class ICTSetupEvaluation:
    symbol: str
    direction: str  # "BUY" or "SELL"
    total_score: float
    grade: SetupGrade
    factors_met: List[str]
    is_valid_entry: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "total_score": self.total_score,
            "grade": self.grade.value,
            "factors_met": self.factors_met,
            "is_valid_entry": self.is_valid_entry,
        }


class ICTMasterConfluenceEngine:
    """
    Combines Smart Money Concepts into a unified trade qualification engine.
    Weights:
    - Market Structure Shift (MSS): 30 pts
    - Fair Value Gap (FVG): 20 pts
    - Order Block (OB): 20 pts
    - Liquidity Sweep: 15 pts
    - Liquidity Void / Rebalance: 15 pts
    """
    WEIGHTS = {
        "mss": 30.0,
        "fvg": 20.0,
        "order_block": 20.0,
        "liquidity_sweep": 15.0,
        "liquidity_void": 15.0,
    }

    def __init__(self, min_score_threshold: float = 60.0):
        if not (0.0 <= min_score_threshold <= 100.0):
            raise ValueError("min_score_threshold must be between 0 and 100")
        self.min_score_threshold = min_score_threshold

    def evaluate_setup(
        self,
        symbol: str,
        direction: str,
        has_mss: bool = False,
        has_fvg: bool = False,
        has_order_block: bool = False,
        has_liquidity_sweep: bool = False,
        has_liquidity_void: bool = False,
    ) -> ICTSetupEvaluation:
        direction_upper = direction.upper()
        if direction_upper not in ["BUY", "SELL"]:
            raise ValueError("Direction must be 'BUY' or 'SELL'")

        score = 0.0
        factors = []

        if has_mss:
            score += self.WEIGHTS["mss"]
            factors.append("Market Structure Shift (MSS)")
        if has_fvg:
            score += self.WEIGHTS["fvg"]
            factors.append("Fair Value Gap (FVG)")
        if has_order_block:
            score += self.WEIGHTS["order_block"]
            factors.append("Order Block (OB)")
        if has_liquidity_sweep:
            score += self.WEIGHTS["liquidity_sweep"]
            factors.append("Liquidity Sweep")
        if has_liquidity_void:
            score += self.WEIGHTS["liquidity_void"]
            factors.append("Liquidity Void Alignment")

        # Determine Grade
        if score >= 80.0:
            grade = SetupGrade.A_PLUS
        elif score >= 60.0:
            grade = SetupGrade.B
        elif score >= 40.0:
            grade = SetupGrade.C
        else:
            grade = SetupGrade.INVALID

        is_valid = score >= self.min_score_threshold

        return ICTSetupEvaluation(
            symbol=symbol,
            direction=direction_upper,
            total_score=score,
            grade=grade,
            factors_met=factors,
            is_valid_entry=is_valid
        )
