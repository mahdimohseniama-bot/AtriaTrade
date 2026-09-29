from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"

@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume: float

@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float = 0.0
    quantity: float = 0.0
    amount: float = 0.0
    status: OrderStatus = OrderStatus.PENDING

    def __post_init__(self):
        # Sync quantity and amount if one of them is passed
        if self.amount > 0 and self.quantity == 0.0:
            self.quantity = self.amount
        elif self.quantity > 0 and self.amount == 0.0:
            self.amount = self.quantity

@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    status: str
    price: float
    quantity: float
    filled_quantity: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
