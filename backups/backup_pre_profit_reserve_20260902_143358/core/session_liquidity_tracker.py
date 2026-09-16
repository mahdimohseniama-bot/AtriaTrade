"""
SMC Session & Asia Range Liquidity Tracker (Capability 88)
Tracks session highs/lows (specifically Asia Range) and detects
London/NY sweeps and directional expansion.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class SessionSweepEvent:
    detected: bool
    sweep_type: str  # "ASIA_HIGH_SWEEP", "ASIA_LOW_SWEEP", "NONE"
    session_high: float
    session_low: float
    swept_level: float
    entry_price: float
    target_opposite_level: float
    suggested_stop_loss: float
    reason: str

class SessionLiquidityTracker:
    def __init__(self, sweep_buffer_pct: float = 0.0005):
        """
        :param sweep_buffer_pct: Small tolerance beyond session level to validate liquidity sweep
        """
        self.sweep_buffer_pct = sweep_buffer_pct

    def track_asia_sweep(
        self,
        current_candle: Dict[str, float],
        asia_high: float,
        asia_low: float,
        current_session: str = "LONDON"
    ) -> SessionSweepEvent:
        """
        Detects if current London/NY candle swept Asia session High/Low and rejected back.
        """
        if asia_high <= asia_low or asia_low <= 0:
            return SessionSweepEvent(
                detected=False,
                sweep_type="NONE",
                session_high=asia_high,
                session_low=asia_low,
                swept_level=0.0,
                entry_price=0.0,
                target_opposite_level=0.0,
                suggested_stop_loss=0.0,
                reason="Invalid Asia session bounds"
            )

        high = float(current_candle.get("high", 0.0))
        low = float(current_candle.get("low", 0.0))
        close = float(current_candle.get("close", 0.0))

        if high <= low:
            return SessionSweepEvent(
                detected=False,
                sweep_type="NONE",
                session_high=asia_high,
                session_low=asia_low,
                swept_level=0.0,
                entry_price=0.0,
                target_opposite_level=0.0,
                suggested_stop_loss=0.0,
                reason="Invalid candle data"
            )

        # 1. Asia High Sweep (Bearish reversal setup: hunted buy-stops above Asia high, closed back inside)
        if high >= asia_high * (1 + self.sweep_buffer_pct) and close < asia_high:
            return SessionSweepEvent(
                detected=True,
                sweep_type="ASIA_HIGH_SWEEP",
                session_high=asia_high,
                session_low=asia_low,
                swept_level=asia_high,
                entry_price=close,
                target_opposite_level=asia_low,
                suggested_stop_loss=high,
                reason=f"{current_session.upper()} session swept Asia High and rejected back inside"
            )

        # 2. Asia Low Sweep (Bullish reversal setup: hunted sell-stops below Asia low, closed back inside)
        if low <= asia_low * (1 - self.sweep_buffer_pct) and close > asia_low:
            return SessionSweepEvent(
                detected=True,
                sweep_type="ASIA_LOW_SWEEP",
                session_high=asia_high,
                session_low=asia_low,
                swept_level=asia_low,
                entry_price=close,
                target_opposite_level=asia_high,
                suggested_stop_loss=low,
                reason=f"{current_session.upper()} session swept Asia Low and rejected back inside"
            )

        return SessionSweepEvent(
            detected=False,
            sweep_type="NONE",
            session_high=asia_high,
            session_low=asia_low,
            swept_level=0.0,
            entry_price=0.0,
            target_opposite_level=0.0,
            suggested_stop_loss=0.0,
            reason="No Asia session liquidity sweep detected"
        )
