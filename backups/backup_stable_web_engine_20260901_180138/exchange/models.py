from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume: float

@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    status: str
    price: float
    quantity: float
    filled_quantity: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
