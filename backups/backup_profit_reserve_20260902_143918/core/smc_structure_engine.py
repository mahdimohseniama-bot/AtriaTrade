"""
Smart Money Concepts (SMC) Structure Engine for AtriaTrade.
Identifies Order Blocks (OB), Break of Structure (BOS), and Change of Character (ChoCH).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from src.core.fvg_detector import Candle


class StructureEventType(str, Enum):
    BOS_BULLISH = "BOS_BULLISH"
    BOS_BEARISH = "BOS_BEARISH"
    CHOCH_BULLISH = "CHOCH_BULLISH"
    CHOCH_BEARISH = "CHOCH_BEARISH"


class OrderBlockType(str, Enum):
    BULLISH = "BULLISH_ORDER_BLOCK"
    BEARISH = "BEARISH_ORDER_BLOCK"


@dataclass(frozen=True)
class OrderBlock:
    ob_type: OrderBlockType
    high: float
    low: float
    candle_index: int
    is_mitigated: bool = False


@dataclass(frozen=True)
class SMCStructureEvent:
    event_type: StructureEventType
    breakout_price: float
    candle_index: int


class SMCStructureEngine:
    """
    Evaluates market swings to detect order blocks and structural shifts (BOS/ChoCH).
    """

    def __init__(self, swing_lookback: int = 3):
        if swing_lookback < 1:
            raise ValueError("swing_lookback باید حداقل ۱ باشد")
        self.swing_lookback = swing_lookback

    def find_swing_highs_lows(self, candles: List[Candle]):
        """
        یافتن سقف‌ها و کف‌های پیوتی محلی بر اساس بازه نگاه به گذشته
        """
        highs = []
        lows = []
        n = len(candles)
        k = self.swing_lookback

        for i in range(k, n - k):
            current_high = candles[i].high
            current_low = candles[i].low

            # Check Swing High
            if all(current_high >= candles[j].high for j in range(i - k, i + k + 1) if j != i):
                highs.append((i, current_high))

            # Check Swing Low
            if all(current_low <= candles[j].low for j in range(i - k, i + k + 1) if j != i):
                lows.append((i, current_low))

        return highs, lows

    def detect_order_blocks(self, candles: List[Candle]) -> List[OrderBlock]:
        """
        اردر بلاک صعودی: آخرین کندل نزولی قبل از یک حرکت صعودی قوی که سقف محلی را می‌شکند.
        اردر بلاک نزولی: آخرین کندل صعودی قبل از یک حرکت نزولی قوی که کف محلی را می‌شکند.
        """
        obs = []
        if len(candles) < 4:
            return obs

        for i in range(1, len(candles) - 1):
            c_prev = candles[i - 1]
            c_curr = candles[i]
            c_next = candles[i + 1]

            # Bullish OB: Bearish candle followed by strong bullish breakout
            if c_curr.close < c_curr.open and c_next.close > c_curr.high and (c_next.close - c_next.open) > (c_curr.open - c_curr.close):
                obs.append(
                    OrderBlock(
                        ob_type=OrderBlockType.BULLISH,
                        high=c_curr.high,
                        low=c_curr.low,
                        candle_index=i,
                        is_mitigated=False
                    )
                )

            # Bearish OB: Bullish candle followed by strong bearish breakdown
            elif c_curr.close > c_curr.open and c_next.close < c_curr.low and (c_next.open - c_next.close) > (c_curr.close - c_curr.open):
                obs.append(
                    OrderBlock(
                        ob_type=OrderBlockType.BEARISH,
                        high=c_curr.high,
                        low=c_curr.low,
                        candle_index=i,
                        is_mitigated=False
                    )
                )

        return obs
