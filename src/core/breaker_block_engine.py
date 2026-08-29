"""
Breaker Block Detection Engine.
Detects failed Order Blocks that get invalidated by a break of structure,
then invert their role (Bullish OB -> Bearish Breaker, Bearish OB -> Bullish Breaker).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BlockRole(str, Enum):
    BULLISH_OB = "BULLISH_OB"
    BEARISH_OB = "BEARISH_OB"
    BULLISH_BREAKER = "BULLISH_BREAKER"  # Inverted Bearish OB (demand above)
    BEARISH_BREAKER = "BEARISH_BREAKER"  # Inverted Bullish OB (supply)


@dataclass
class BreakerBlock:
    original_role: BlockRole
    new_role: BlockRole
    block_top: float
    block_bottom: float
    break_candle_close: float
    mid_price: float  # 50% level of the breaker zone (ICT entry reference)
    description: str


class BreakerBlockEngine:
    """
    Detects Order Block invalidations and converts them into Breaker Blocks.
    """

    def __init__(self, min_close_beyond: float = 0.0):
        """
        Args:
            min_close_beyond: Minimum distance the close must travel beyond
                              the block edge to count as a valid break.
        """
        self.min_close_beyond = min_close_beyond

    def check_invalidation(
        self,
        block_role: BlockRole,
        block_top: float,
        block_bottom: float,
        break_close: float
    ) -> Optional[BreakerBlock]:
        """
        Checks whether a close beyond the block invalidates it and creates a Breaker.

        Args:
            block_role: Current role of the block (BULLISH_OB or BEARISH_OB)
            block_top: Top price of the original block
            block_bottom: Bottom price of the original block
            break_close: The closing price of the candle that may have broken the block

        Returns:
            BreakerBlock if inversion occurred, otherwise None.
        """
        if block_top <= block_bottom:
            raise ValueError("block_top must be greater than block_bottom")

        mid = (block_top + block_bottom) / 2.0

        if block_role == BlockRole.BULLISH_OB:
            # Bullish OB broken when price CLOSES below block_bottom
            if break_close < block_bottom - self.min_close_beyond:
                return BreakerBlock(
                    original_role=block_role,
                    new_role=BlockRole.BEARISH_BREAKER,
                    block_top=block_top,
                    block_bottom=block_bottom,
                    break_candle_close=break_close,
                    mid_price=mid,
                    description=(
                        f"Bearish Breaker formed: Bullish OB [{block_bottom}-{block_top}] "
                        f"invalidated by close at {break_close}. acts as supply."
                    )
                )

        elif block_role == BlockRole.BEARISH_OB:
            # Bearish OB broken when price CLOSES above block_top
            if break_close > block_top + self.min_close_beyond:
                return BreakerBlock(
                    original_role=block_role,
                    new_role=BlockRole.BULLISH_BREAKER,
                    block_top=block_top,
                    block_bottom=block_bottom,
                    break_candle_close=break_close,
                    mid_price=mid,
                    description=(
                        f"Bullish Breaker formed: Bearish OB [{block_bottom}-{block_top}] "
                        f"invalidated by close at {break_close}. acts as demand."
                    )
                )

        # No invalidation: block is still intact
        return None

    def is_retest_valid(self, breaker: BreakerBlock, retest_price: float, direction: str) -> bool:
        """
        Validates whether a retest touches the breaker zone correctly.

        Args:
            breaker: The detected BreakerBlock
            retest_price: Price returning to the breaker zone
            direction: "SHORT" for bearish breaker retest, "LONG" for bullish breaker retest
        """
        in_zone = breaker.block_bottom <= retest_price <= breaker.block_top
        if direction.upper() == "SHORT":
            return in_zone and breaker.new_role == BlockRole.BEARISH_BREAKER
        elif direction.upper() == "LONG":
            return in_zone and breaker.new_role == BlockRole.BULLISH_BREAKER
        return False
