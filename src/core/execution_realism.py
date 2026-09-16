from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class SlippageModelType(str, Enum):
    NONE = "none"
    FIXED_PERCENTAGE = "fixed_percentage"
    FIXED_POINTS = "fixed_points"
    VOLUME_IMPACT = "volume_impact"

@dataclass
class FeeConfig:
    maker_fee_rate: float = 0.001   # 0.1% standard spot maker
    taker_fee_rate: float = 0.001   # 0.1% standard spot taker
    fixed_fee_per_trade: float = 0.0

@dataclass
class SlippageConfig:
    model: SlippageModelType = SlippageModelType.FIXED_PERCENTAGE
    slippage_percent: float = 0.0005  # 0.05% default slippage
    slippage_points: float = 0.0
    impact_factor: float = 0.01      # For volume impact: impact * (order_vol / bar_vol)

@dataclass
class LatencyConfig:
    simulated_latency_ms: int = 50   # 50ms default network + matching engine latency

@dataclass
class ExecutionResult:
    original_price: float
    executed_price: float
    quantity: float
    side: str
    fee_amount: float
    slippage_cost: float
    latency_ms: int
    net_value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_price": self.original_price,
            "executed_price": self.executed_price,
            "quantity": self.quantity,
            "side": self.side,
            "fee_amount": self.fee_amount,
            "slippage_cost": self.slippage_cost,
            "latency_ms": self.latency_ms,
            "net_value": self.net_value,
        }

class ExecutionRealismModel:
    def __init__(
        self,
        fee_config: Optional[FeeConfig] = None,
        slippage_config: Optional[SlippageConfig] = None,
        latency_config: Optional[LatencyConfig] = None,
    ):
        self.fee_config = fee_config or FeeConfig()
        self.slippage_config = slippage_config or SlippageConfig()
        self.latency_config = latency_config or LatencyConfig()

    def calculate_slippage(
        self,
        price: float,
        quantity: float,
        side: str,
        bar_volume: Optional[float] = None
    ) -> float:
        """
        Calculates execution price adjustment due to slippage.
        BUY: executed price is higher than requested.
        SELL: executed price is lower than requested.
        """
        side_norm = side.upper()
        if self.slippage_config.model == SlippageModelType.NONE:
            return price

        shift = 0.0
        if self.slippage_config.model == SlippageModelType.FIXED_PERCENTAGE:
            shift = price * self.slippage_config.slippage_percent

        elif self.slippage_config.model == SlippageModelType.FIXED_POINTS:
            shift = self.slippage_config.slippage_points

        elif self.slippage_config.model == SlippageModelType.VOLUME_IMPACT:
            if bar_volume and bar_volume > 0:
                volume_ratio = quantity / bar_volume
                shift = price * (self.slippage_config.impact_factor * volume_ratio)
            else:
                shift = price * self.slippage_config.slippage_percent

        if side_norm in ["BUY", "LONG"]:
            return price + shift
        elif side_norm in ["SELL", "SHORT"]:
            return max(0.00000001, price - shift)
        return price

    def calculate_fee(
        self,
        executed_price: float,
        quantity: float,
        is_maker: bool = False
    ) -> float:
        """
        Calculates commission/fee for trade volume.
        """
        trade_value = executed_price * quantity
        rate = self.fee_config.maker_fee_rate if is_maker else self.fee_config.taker_fee_rate
        return (trade_value * rate) + self.fee_config.fixed_fee_per_trade

    def apply_realism(
        self,
        price: float,
        quantity: float,
        side: str,
        is_maker: bool = False,
        bar_volume: Optional[float] = None,
    ) -> ExecutionResult:
        """
        Simulates realistic fill price, fees, and latency for an order.
        """
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        side_norm = side.upper()
        if side_norm not in ["BUY", "SELL", "LONG", "SHORT"]:
            raise ValueError(f"Invalid order side: {side}")

        executed_price = self.calculate_slippage(
            price=price,
            quantity=quantity,
            side=side_norm,
            bar_volume=bar_volume
        )

        slippage_cost = abs(executed_price - price) * quantity
        fee_amount = self.calculate_fee(executed_price, quantity, is_maker=is_maker)

        trade_value = executed_price * quantity
        if side_norm in ["BUY", "LONG"]:
            net_value = trade_value + fee_amount
        else:
            net_value = trade_value - fee_amount

        return ExecutionResult(
            original_price=price,
            executed_price=executed_price,
            quantity=quantity,
            side=side_norm,
            fee_amount=fee_amount,
            slippage_cost=slippage_cost,
            latency_ms=self.latency_config.simulated_latency_ms,
            net_value=net_value,
        )
