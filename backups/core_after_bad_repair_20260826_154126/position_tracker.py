import time
from typing import Any, Dict, Optional


class PositionDict(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(
                f"'PositionDict' object has no attribute '{name}'"
            ) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class PositionTracker:
    def __init__(self, **kwargs: Any) -> None:
        self.positions: Dict[str, PositionDict] = {}

    def get_position(self, symbol: str) -> Optional[PositionDict]:
        return self.positions.get(str(symbol).upper())

    def update_position(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        entry_price: Optional[float] = None,
        **kwargs: Any,
    ) -> PositionDict:
        qty = kwargs.get("size", quantity)
        price = kwargs.get("price", entry_price)

        if qty is None:
            raise ValueError("quantity or size is required")
        if price is None:
            raise ValueError("entry_price or price is required")

        symbol = str(symbol).upper()
        qty = float(qty)
        price = float(price)

        position = PositionDict({
            "symbol": symbol,
            "side": str(getattr(side, "value", side)).upper(),
            "quantity": qty,
            "size": qty,
            "entry_price": price,
            "price": price,
            "sl": kwargs.get("sl", kwargs.get("stop_loss")),
            "tp": kwargs.get("tp", kwargs.get("take_profit")),
            "status": "OPEN",
            "updated_at": time.time(),
        })
        self.positions[symbol] = position
        return position

    def open_position(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        **kwargs: Any,
    ) -> PositionDict:
        return self.update_position(
            symbol=symbol,
            side=side,
            quantity=kwargs.get("size", quantity),
            entry_price=kwargs.get("entry_price", price),
            **kwargs,
        )

    def close_position(self, symbol: str, **kwargs: Any) -> Optional[PositionDict]:
        return self.positions.pop(str(symbol).upper(), None)
