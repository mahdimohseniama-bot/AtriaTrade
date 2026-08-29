"""
Smart Money Tool (SMT) Divergence Engine.
Detects non-symmetrical swing highs/lows between correlated asset pairs (e.g., BTC vs ETH).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any


class SMTType(str, Enum):
    BULLISH = "BULLISH_SMT"  # Asset A made LL, Asset B made HL (Smart Money Accumulation)
    BEARISH = "BEARISH_SMT"  # Asset A made HH, Asset B made LH (Smart Money Distribution)
    NONE = "NO_DIVERGENCE"


@dataclass
class SMTResult:
    divergence_type: SMTType
    primary_asset: str
    correlated_asset: str
    primary_swing: str  # "HH", "LL", "LH", "HL"
    correlated_swing: str  # "HH", "LL", "LH", "HL"
    confidence_boost: float
    description: str


class SMTDivergenceEngine:
    """
    Engine to detect SMT Divergences across correlated asset swing structures.
    """

    def __init__(self, default_boost: float = 0.25):
        self.default_boost = default_boost

    def detect_divergence(
        self,
        primary_asset: str,
        primary_prev_swing: float,
        primary_curr_swing: float,
        correlated_asset: str,
        correlated_prev_swing: float,
        correlated_curr_swing: float,
        swing_type: str  # "HIGH" or "LOW"
    ) -> SMTResult:
        """
        Detects if an SMT Divergence exists between two correlated swings.
        
        Args:
            primary_asset: Name of primary symbol (e.g., "BTCUSDT")
            primary_prev_swing: Previous swing high/low price of primary asset
            primary_curr_swing: Current swing high/low price of primary asset
            correlated_asset: Name of correlated symbol (e.g., "ETHUSDT")
            correlated_prev_swing: Previous swing high/low price of correlated asset
            correlated_curr_swing: Current swing high/low price of correlated asset
            swing_type: "HIGH" for comparing swing highs, "LOW" for comparing swing lows
        """
        if swing_type.upper() == "LOW":
            # Check swing lows
            primary_is_lower_low = primary_curr_swing < primary_prev_swing
            correlated_is_higher_low = correlated_curr_swing >= correlated_prev_swing

            primary_is_higher_low = primary_curr_swing >= primary_prev_swing
            correlated_is_lower_low = correlated_curr_swing < correlated_prev_swing

            # Bullish SMT: One makes Lower Low, the other fails and makes Higher Low
            if primary_is_lower_low and correlated_is_higher_low:
                return SMTResult(
                    divergence_type=SMTType.BULLISH,
                    primary_asset=primary_asset,
                    correlated_asset=correlated_asset,
                    primary_swing="LL",
                    correlated_swing="HL",
                    confidence_boost=self.default_boost,
                    description=f"Bullish SMT: {primary_asset} made Lower Low while {correlated_asset} made Higher Low (Accumulation)."
                )
            elif primary_is_higher_low and correlated_is_lower_low:
                return SMTResult(
                    divergence_type=SMTType.BULLISH,
                    primary_asset=primary_asset,
                    correlated_asset=correlated_asset,
                    primary_swing="HL",
                    correlated_swing="LL",
                    confidence_boost=self.default_boost,
                    description=f"Bullish SMT: {primary_asset} made Higher Low while {correlated_asset} made Lower Low (Accumulation)."
                )

        elif swing_type.upper() == "HIGH":
            # Check swing highs
            primary_is_higher_high = primary_curr_swing > primary_prev_swing
            correlated_is_lower_high = correlated_curr_swing <= correlated_prev_swing

            primary_is_lower_high = primary_curr_swing <= primary_prev_swing
            correlated_is_higher_high = correlated_curr_swing > correlated_prev_swing

            # Bearish SMT: One makes Higher High, the other fails and makes Lower High
            if primary_is_higher_high and correlated_is_lower_high:
                return SMTResult(
                    divergence_type=SMTType.BEARISH,
                    primary_asset=primary_asset,
                    correlated_asset=correlated_asset,
                    primary_swing="HH",
                    correlated_swing="LH",
                    confidence_boost=self.default_boost,
                    description=f"Bearish SMT: {primary_asset} made Higher High while {correlated_asset} made Lower High (Distribution)."
                )
            elif primary_is_lower_high and correlated_is_higher_high:
                return SMTResult(
                    divergence_type=SMTType.BEARISH,
                    primary_asset=primary_asset,
                    correlated_asset=correlated_asset,
                    primary_swing="LH",
                    correlated_swing="HH",
                    confidence_boost=self.default_boost,
                    description=f"Bearish SMT: {primary_asset} made Lower High while {correlated_asset} made Higher High (Distribution)."
                )

        return SMTResult(
            divergence_type=SMTType.NONE,
            primary_asset=primary_asset,
            correlated_asset=correlated_asset,
            primary_swing="SYNC",
            correlated_swing="SYNC",
            confidence_boost=0.0,
            description="No SMT divergence detected. Swings are correlated and symmetrical."
        )
