"""
SMC Strategy: Combines Optimal Trade Entry (OTE) and Fair Value Gap (FVG)
to generate high-probability trade setups with precise risk parameters.
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from src.core.fvg_detector import FVGDetector, Candle, FairValueGap, FVGType
from src.core.ote_engine import OTEEngine, OTEProfile, TradeDirection


class SignalDirection(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class SMCSignal:
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    fvg_zone: Optional[FairValueGap] = None
    ote_level: Optional[float] = None
    reason: str = ""


class SMCStrategy:
    def __init__(self, min_gap_percent: float = 0.1, sweet_spot: float = 0.705):
        self.fvg_detector = FVGDetector(min_gap_percent=min_gap_percent)
        self.ote_engine = OTEEngine(sweet_spot=sweet_spot)

    def analyze(self, candles: List[Candle], swing_high: float, swing_low: float) -> SMCSignal:
        if len(candles) < 3 or swing_high <= swing_low:
            return SMCSignal(
                direction=SignalDirection.NEUTRAL,
                entry_price=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                risk_reward_ratio=0.0,
                reason="Insufficient candles or invalid swing levels"
            )

        fvgs: List[FairValueGap] = self.fvg_detector.detect_fvgs(candles)
        current_price = candles[-1].close

        # Bullish setup (LONG): Retracement into Discount OTE
        bullish_profile: OTEProfile = self.ote_engine.calculate_ote(
            swing_low=swing_low, swing_high=swing_high, direction=TradeDirection.LONG
        )
        bullish_fvgs = [f for f in fvgs if f.gap_type == FVGType.BULLISH and not f.is_mitigated]

        for fvg in bullish_fvgs:
            if fvg.bottom_price <= bullish_profile.ote_705 <= fvg.top_price or \
               (bullish_profile.ote_786 <= fvg.top_price <= bullish_profile.ote_618):
                entry = bullish_profile.ote_705
                sl = swing_low * 0.998
                tp = bullish_profile.target_ext_27
                risk = entry - sl
                reward = tp - entry
                rr = round(reward / risk, 2) if risk > 0 else 0.0

                if rr >= 1.5:
                    return SMCSignal(
                        direction=SignalDirection.BUY,
                        entry_price=round(entry, 4),
                        stop_loss=round(sl, 4),
                        take_profit=round(tp, 4),
                        risk_reward_ratio=rr,
                        fvg_zone=fvg,
                        ote_level=bullish_profile.ote_705,
                        reason=f"Bullish OTE (0.705: {entry:.2f}) aligned with Bullish FVG [{fvg.bottom_price:.2f} - {fvg.top_price:.2f}]"
                    )

        # Bearish setup (SHORT): Retracement into Premium OTE
        bearish_profile: OTEProfile = self.ote_engine.calculate_ote(
            swing_low=swing_low, swing_high=swing_high, direction=TradeDirection.SHORT
        )
        bearish_fvgs = [f for f in fvgs if f.gap_type == FVGType.BEARISH and not f.is_mitigated]

        for fvg in bearish_fvgs:
            if fvg.bottom_price <= bearish_profile.ote_705 <= fvg.top_price or \
               (bearish_profile.ote_618 <= fvg.bottom_price <= bearish_profile.ote_786):
                entry = bearish_profile.ote_705
                sl = swing_high * 1.002
                tp = bearish_profile.target_ext_27
                risk = sl - entry
                reward = entry - tp
                rr = round(reward / risk, 2) if risk > 0 else 0.0

                if rr >= 1.5:
                    return SMCSignal(
                        direction=SignalDirection.SELL,
                        entry_price=round(entry, 4),
                        stop_loss=round(sl, 4),
                        take_profit=round(tp, 4),
                        risk_reward_ratio=rr,
                        fvg_zone=fvg,
                        ote_level=bearish_profile.ote_705,
                        reason=f"Bearish OTE (0.705: {entry:.2f}) aligned with Bearish FVG [{fvg.bottom_price:.2f} - {fvg.top_price:.2f}]"
                    )

        return SMCSignal(
            direction=SignalDirection.NEUTRAL,
            entry_price=current_price,
            stop_loss=0.0,
            take_profit=0.0,
            risk_reward_ratio=0.0,
            reason="No high-probability confluence detected between OTE and FVG"
        )
