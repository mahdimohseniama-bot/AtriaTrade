"""ردیابی پوزیشن‌های باز و بسته‌شده — AtriaTrade"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Position:
    """اطلاعات یک پوزیشن"""

    symbol: str
    side: str
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_id: str = field(
        default_factory=lambda: uuid.uuid4().hex
    )
    opened_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    closed_at: Optional[str] = None
    realized_pnl: Optional[float] = None
    close_reason: Optional[str] = None

    def unrealized_pnl(self, current_price: float) -> float:
        """محاسبه سود یا زیان تحقق‌نیافته"""

        if current_price is None or current_price <= 0:
            raise ValueError(
                "current_price باید بزرگ‌تر از صفر باشد"
            )

        if self.side == "BUY":
            price_difference = current_price - self.entry_price
        elif self.side == "SELL":
            price_difference = self.entry_price - current_price
        else:
            raise ValueError("side باید BUY یا SELL باشد")

        return price_difference * self.quantity

    def to_dict(self) -> dict:
        """تبدیل اطلاعات پوزیشن به دیکشنری"""

        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "realized_pnl": self.realized_pnl,
            "close_reason": self.close_reason,
        }


def normalize_side(side) -> str:
    """تبدیل OrderSide یا رشته به BUY یا SELL"""

    if hasattr(side, "value"):
        normalized = str(side.value).upper()
    else:
        normalized = str(side).upper()

    if normalized not in ("BUY", "SELL"):
        raise ValueError("side باید BUY یا SELL باشد")

    return normalized


class PositionTracker:
    """مدیریت پوزیشن‌های باز و سوابق پوزیشن‌های بسته‌شده"""

    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}
        self._closed_positions: list[Position] = []

    def open_position(
        self,
        symbol: str,
        side,
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Position:
        """باز کردن یک پوزیشن جدید"""

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol نباید خالی باشد")

        symbol = symbol.strip().upper()

        if symbol in self._positions:
            raise ValueError(
                f"برای نماد {symbol} از قبل پوزیشن باز وجود دارد"
            )

        if entry_price is None or entry_price <= 0:
            raise ValueError(
                "entry_price باید بزرگ‌تر از صفر باشد"
            )

        if quantity is None or quantity <= 0:
            raise ValueError(
                "quantity باید بزرگ‌تر از صفر باشد"
            )

        position = Position(
            symbol=symbol,
            side=normalize_side(side),
            entry_price=float(entry_price),
            quantity=float(quantity),
            stop_loss=(
                float(stop_loss)
                if stop_loss is not None
                else None
            ),
            take_profit=(
                float(take_profit)
                if take_profit is not None
                else None
            ),
        )

        self._positions[symbol] = position
        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: Optional[str] = None,
    ) -> Position:
        """بستن پوزیشن و محاسبه سود یا زیان تحقق‌یافته"""

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol نباید خالی باشد")

        symbol = symbol.strip().upper()
        position = self._positions.get(symbol)

        if position is None:
            raise KeyError(
                f"برای نماد {symbol} پوزیشن بازی وجود ندارد"
            )

        if exit_price is None or exit_price <= 0:
            raise ValueError(
                "exit_price باید بزرگ‌تر از صفر باشد"
            )

        if position.side == "BUY":
            pnl = (
                exit_price - position.entry_price
            ) * position.quantity
        else:
            pnl = (
                position.entry_price - exit_price
            ) * position.quantity

        position.closed_at = datetime.now(
            timezone.utc
        ).isoformat()
        position.realized_pnl = float(pnl)
        position.close_reason = reason

        self._closed_positions.append(position)
        del self._positions[symbol]

        return position

    def get_position(
        self,
        symbol: str,
    ) -> Optional[Position]:
        """دریافت پوزیشن باز یک نماد"""

        if not isinstance(symbol, str):
            return None

        return self._positions.get(symbol.strip().upper())

    def get_open_positions(self) -> list[Position]:
        """دریافت تمام پوزیشن‌های باز"""

        return list(self._positions.values())

    def get_closed_positions(self) -> list[Position]:
        """دریافت تمام پوزیشن‌های بسته‌شده"""

        return list(self._closed_positions)

    def get_status(self) -> dict:
        """دریافت وضعیت کلی پوزیشن‌ها"""

        total_realized_pnl = sum(
            position.realized_pnl or 0.0
            for position in self._closed_positions
        )

        return {
            "open_positions": [
                position.to_dict()
                for position in self._positions.values()
            ],
            "closed_positions_count": len(
                self._closed_positions
            ),
            "total_realized_pnl": round(
                total_realized_pnl,
                8,
            ),
        }
