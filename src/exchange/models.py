from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume: float = 0.0

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def keys(self):
        return ["symbol", "bid", "ask", "last_price", "volume"]

@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    status: str
    price: float
    quantity: float
    filled_quantity: float
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)
