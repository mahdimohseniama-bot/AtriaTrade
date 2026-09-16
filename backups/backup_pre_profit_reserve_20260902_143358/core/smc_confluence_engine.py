"""
SMC Confluence Strategy and Signal Engine for AtriaTrade (Capability 74).
Aggregates Order Blocks, FVGs, Liquidity Sweeps, OTE levels, and Killzones into unified institutional trade signals.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict


class SMCAction(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class SMCConfluenceResult:
    action: SMCAction
    score: int
    max_score: int
    confidence_pct: float
    reasons: List[str]
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class SMCConfluenceEngine:
    def __init__(self, min_confidence_threshold: float = 60.0):
        if not (0.0 <= min_confidence_threshold <= 100.0):
            raise ValueError("Confidence threshold must be between 0 and 100")
        self.min_confidence_threshold = min_confidence_threshold

    def evaluate_setup(
        self,
        is_killzone: bool,
        has_liquidity_sweep: bool,
        has_market_structure_shift: bool,
        is_in_ote_zone: bool,
        has_order_block: bool,
        has_fvg_alignment: bool,
        direction: str = "BULLISH",
        entry_price: Optional[float] = None,
        suggested_sl: Optional[float] = None,
        suggested_tp: Optional[float] = None
    ) -> SMCConfluenceResult:
        score = 0
        max_score = 100
        reasons = []

        # ۱. همزمانی با کیل‌زون سشن‌های معاملاتی (وزن: ۲۰)
        if is_killzone:
            score += 20
            reasons.append("KILLZONE_ACTIVE")

        # ۲. هانت استاپ و جاروی نقدینگی (وزن: ۲۵)
        if has_liquidity_sweep:
            score += 25
            reasons.append("LIQUIDITY_SWEEP_CONFIRMED")

        # ۳. شکست ساختار یا تغییر روند (وزن: ۲۰)
        if has_market_structure_shift:
            score += 20
            reasons.append("STRUCTURE_SHIFT_CONFIRMED")

        # ۴. ورود در محدوده طلایی فیبوناچی (وزن: ۱۵)
        if is_in_ote_zone:
            score += 15
            reasons.append("IN_OTE_ZONE")

        # ۵. تلاقی با اردر بلاک (وزن: ۱۰)
        if has_order_block:
            score += 10
            reasons.append("ORDER_BLOCK_CONFLUENCE")

        # ۶. پر شدن گپ ارزش منصفانه FVG (وزن: ۱۰)
        if has_fvg_alignment:
            score += 10
            reasons.append("FVG_ALIGNMENT")

        confidence = (score / max_score) * 100.0

        if confidence < self.min_confidence_threshold:
            action = SMCAction.HOLD
        else:
            if direction.upper() == "BULLISH":
                action = SMCAction.STRONG_BUY if confidence >= 80.0 else SMCAction.BUY
            else:
                action = SMCAction.STRONG_SELL if confidence >= 80.0 else SMCAction.SELL

        return SMCConfluenceResult(
            action=action,
            score=score,
            max_score=max_score,
            confidence_pct=round(confidence, 2),
            reasons=reasons,
            stop_loss=suggested_sl,
            take_profit=suggested_tp
        )
