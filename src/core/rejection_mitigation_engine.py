"""
Rejection Block & Mitigation Block Detection Engine.
Identifies high-liquidity rejection wicks (Rejection Blocks)
and failure-swing order block flips (Mitigation Blocks).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BlockType(str, Enum):
    BULLISH_REJECTION = "BULLISH_REJECTION"
    BEARISH_REJECTION = "BEARISH_REJECTION"
    BULLISH_MITIGATION = "BULLISH_MITIGATION"
    BEARISH_MITIGATION = "BEARISH_MITIGATION"


@dataclass
class RejectionBlock:
    block_type: BlockType
    high: float
    low: float
    wick_start: float  # Top/bottom of body where wick starts
    wick_extreme: float  # The extreme price reached by the wick
    description: str


@dataclass
class MitigationBlock:
    block_type: BlockType
    block_top: float
    block_bottom: float
    mid_price: float
    description: str


class RejectionMitigationEngine:
    """
    Engine to identify Rejection Blocks (wick based) and Mitigation Blocks (failure-swing based).
    """

    def __init__(self, min_wick_ratio: float = 0.5):
        """
        Args:
            min_wick_ratio: Minimum ratio of the wick relative to total candle range
                            to qualify as a strong rejection.
        """
        self.min_wick_ratio = min_wick_ratio

    def detect_rejection_block(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float
    ) -> Optional[RejectionBlock]:
        """
        Detects strong candle wick rejections.
        """
        candle_range = high_price - low_price
        if candle_range <= 0:
            return None

        body_top = max(open_price, close_price)
        body_bottom = min(open_price, close_price)

        upper_wick = high_price - body_top
        lower_wick = body_bottom - low_price

        # Check for Bearish Rejection (Long Upper Wick)
        if (upper_wick / candle_range) >= self.min_wick_ratio:
            return RejectionBlock(
                block_type=BlockType.BEARISH_REJECTION,
                high=high_price,
                low=body_top,
                wick_start=body_top,
                wick_extreme=high_price,
                description=f"Bearish Rejection Block in zone [{body_top:.2f} - {high_price:.2f}]"
            )

        # Check for Bullish Rejection (Long Lower Wick)
        if (lower_wick / candle_range) >= self.min_wick_ratio:
            return RejectionBlock(
                block_type=BlockType.BULLISH_REJECTION,
                high=body_bottom,
                low=low_price,
                wick_start=body_bottom,
                wick_extreme=low_price,
                description=f"Bullish Rejection Block in zone [{low_price:.2f} - {body_bottom:.2f}]"
            )

        return None

    def detect_mitigation_block(
        self,
        is_failure_swing: bool,
        block_top: float,
        block_bottom: float,
        break_close: float,
        direction: str
    ) -> Optional[MitigationBlock]:
        """
        Detects Mitigation Block when a swing failure is followed by structural break.

        Args:
            is_failure_swing: True if swing did not take out the prior swing high/low.
            block_top: High of the un-swept order block.
            block_bottom: Low of the un-swept order block.
            break_close: Close price that broke the structure.
            direction: "BEARISH" (breaking downwards) or "BULLISH" (breaking upwards).
        """
        if not is_failure_swing:
            return None

        if block_top <= block_bottom:
            raise ValueError("block_top must be greater than block_bottom")

        mid = (block_top + block_bottom) / 2.0

        if direction.upper() == "BEARISH" and break_close < block_bottom:
            return MitigationBlock(
                block_type=BlockType.BEARISH_MITIGATION,
                block_top=block_top,
                block_bottom=block_bottom,
                mid_price=mid,
                description=f"Bearish Mitigation Block active at [{block_bottom:.2f} - {block_top:.2f}]"
            )

        elif direction.upper() == "BULLISH" and break_close > block_top:
            return MitigationBlock(
                block_type=BlockType.BULLISH_MITIGATION,
                block_top=block_top,
                block_bottom=block_bottom,
                mid_price=mid,
                description=f"Bullish Mitigation Block active at [{block_bottom:.2f} - {block_top:.2f}]"
            )

        return None
