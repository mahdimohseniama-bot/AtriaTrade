"""
AtriaTrade - Position Tracker
Manages active positions, PnL calculations, and tracking history.
"""

from typing import Dict, Any, List, Optional
import time

class Position:
    def __init__(self, position_id: str, symbol: str, side: str, size: float, entry_price: float):
        self.position_id = str(position_id)
        self.symbol = symbol.upper()
        self.side = side.upper()
        self.size = float(size)
        self.entry_price = float(entry_price)
        self.current_price = float(entry_price)
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.opened_at = time.time()
        self.closed_at: Optional[float] = None
        self.is_open = True

    def update_price(self, current_price: float):
        self.current_price = float(current_price)
        if self.side == "BUY":
            self.unrealized_pnl = (self.current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - self.current_price) * self.size

    def close(self, exit_price: float) -> float:
        self.update_price(exit_price)
        self.realized_pnl = self.unrealized_pnl
        self.unrealized_pnl = 0.0
        self.is_open = False
        self.closed_at = time.time()
        return self.realized_pnl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "is_open": self.is_open,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


class PositionTracker:
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []

    def open_position(self, *args, **kwargs) -> Position:
        """
        Supports flexible arguments:
        open_position(symbol, side, size/quantity, entry_price) or keyword args.
        """
        symbol = kwargs.get("symbol")
        side = kwargs.get("side", "BUY")
        size = kwargs.get("size", kwargs.get("quantity", kwargs.get("amount", 0.0)))
        entry_price = kwargs.get("entry_price", kwargs.get("price", 0.0))
        position_id = kwargs.get("position_id")

        if args:
            if len(args) >= 1 and not symbol:
                symbol = args[0]
            if len(args) >= 2 and "side" not in kwargs:
                side = args[1]
            if len(args) >= 3 and size == 0.0:
                size = args[2]
            if len(args) >= 4 and entry_price == 0.0:
                entry_price = args[3]

        if not position_id:
            position_id = f"pos_{len(self.positions) + len(self.closed_positions) + 1}_{int(time.time()*1000)}"

        pos = Position(
            position_id=position_id,
            symbol=str(symbol),
            side=str(side),
            size=float(size),
            entry_price=float(entry_price)
        )
        self.positions[pos.position_id] = pos
        return pos

    def close_position(self, position_id: str, exit_price: float) -> Optional[Dict[str, Any]]:
        if position_id not in self.positions:
            return None
        pos = self.positions.pop(position_id)
        pos.close(exit_price)
        self.closed_positions.append(pos)
        return pos.to_dict()

    def update_prices(self, price_map: Dict[str, float]):
        for pos in self.positions.values():
            if pos.symbol in price_map:
                pos.update_price(price_map[pos.symbol])

    def get_open_positions(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self.positions.values()]

    def get_total_unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_position(self, position_id: str) -> Optional[Position]:
        return self.positions.get(position_id)
