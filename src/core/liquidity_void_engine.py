from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class VoidType(str, Enum):
    BULLISH_VOID = "BULLISH_VOID"
    BEARISH_VOID = "BEARISH_VOID"


class VoidStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FULLY_REBALANCED = "FULLY_REBALANCED"


@dataclass
class LiquidityVoid:
    void_id: str
    void_type: VoidType
    top_price: float
    bottom_price: float
    ce_price: float  # Consequent Encroachment (50% midpoint)
    expansion_range: float
    status: VoidStatus = VoidStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "void_id": self.void_id,
            "void_type": self.void_type.value,
            "top_price": self.top_price,
            "bottom_price": self.bottom_price,
            "ce_price": self.ce_price,
            "expansion_range": self.expansion_range,
            "status": self.status.value,
        }


class LiquidityVoidEngine:
    def __init__(self, expansion_multiplier: float = 2.0):
        if expansion_multiplier <= 1.0:
            raise ValueError("expansion_multiplier must be greater than 1.0")
        self.expansion_multiplier = expansion_multiplier

    def detect_void(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        avg_body_size: float,
        void_id: str = "void_1"
    ) -> Optional[LiquidityVoid]:
        if high_price < low_price or avg_body_size <= 0:
            raise ValueError("Invalid candle metrics or non-positive avg_body_size")

        body_size = abs(close_price - open_price)
        candle_range = high_price - low_price

        # Must be an explosive displacement candle:
        # 1. Body is greater than expansion threshold
        # 2. Body dominates at least 70% of the entire range
        if candle_range <= 0 or (body_size / candle_range) < 0.70:
            return None

        if body_size < (avg_body_size * self.expansion_multiplier):
            return None

        if close_price > open_price:
            v_type = VoidType.BULLISH_VOID
            top = close_price
            bottom = open_price
        else:
            v_type = VoidType.BEARISH_VOID
            top = open_price
            bottom = close_price

        ce = round((top + bottom) / 2.0, 4)
        expansion_range = round(top - bottom, 4)

        return LiquidityVoid(
            void_id=void_id,
            void_type=v_type,
            top_price=top,
            bottom_price=bottom,
            ce_price=ce,
            expansion_range=expansion_range,
            status=VoidStatus.ACTIVE
        )

    def update_void_status(
        self,
        void: LiquidityVoid,
        current_high: float,
        current_low: float
    ) -> VoidStatus:
        if current_high < current_low:
            raise ValueError("current_high cannot be less than current_low")

        if void.status == VoidStatus.FULLY_REBALANCED:
            return void.status

        if void.void_type == VoidType.BULLISH_VOID:
            if current_low <= void.bottom_price:
                void.status = VoidStatus.FULLY_REBALANCED
            elif current_low <= void.ce_price:
                if void.status == VoidStatus.ACTIVE:
                    void.status = VoidStatus.PARTIALLY_FILLED
        elif void.void_type == VoidType.BEARISH_VOID:
            if current_high >= void.top_price:
                void.status = VoidStatus.FULLY_REBALANCED
            elif current_high >= void.ce_price:
                if void.status == VoidStatus.ACTIVE:
                    void.status = VoidStatus.PARTIALLY_FILLED

        return void.status
