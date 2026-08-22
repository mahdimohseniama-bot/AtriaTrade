from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .paper_session import PaperSession


class PaperTradingEngine:
    """
    موتور معاملات آزمایشی AtriaTrade.

    این کلاس هیچ سفارش واقعی به صرافی ارسال نمی‌کند.
    """

    VALID_SIDES = {"BUY", "SELL", "LONG", "SHORT"}

    def __init__(self, session: PaperSession) -> None:
        if not isinstance(session, PaperSession):
            raise TypeError("session باید از نوع PaperSession باشد.")

        self.session = session

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def calculate_pnl(
        self,
        side: str,
        entry_price: float,
        exit_price: float,
        position_size: float,
    ) -> float:
        """
        محاسبه سود و زیان ناخالص معامله.
        """

        side = side.upper().strip()

        if side not in self.VALID_SIDES:
            raise ValueError(
                "سمت معامله نامعتبر است. مقادیر مجاز: BUY, SELL, LONG, SHORT"
            )

        if entry_price <= 0:
            raise ValueError("entry_price باید بزرگ‌تر از صفر باشد.")

        if exit_price <= 0:
            raise ValueError("exit_price باید بزرگ‌تر از صفر باشد.")

        if position_size <= 0:
            raise ValueError("position_size باید بزرگ‌تر از صفر باشد.")

        if side in {"BUY", "LONG"}:
            return (exit_price - entry_price) * position_size

        return (entry_price - exit_price) * position_size

    def execute_paper_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        position_size: float,
        fees: float = 0.0,
        leverage: float = 1.0,
    ) -> Dict[str, Any]:
        """
        اجرای یک معامله آزمایشی بسته‌شده و ثبت آن در نشست.
        """

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol نمی‌تواند خالی باشد.")

        if fees < 0:
            raise ValueError("fees نمی‌تواند منفی باشد.")

        gross_pnl = self.calculate_pnl(
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            position_size=position_size,
        )

        trade_record = self.session.record_trade(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            size=position_size,
            pnl=gross_pnl,
            leverage=leverage,
            fees=fees,
        )

        return {
            "success": True,
            "symbol": symbol.upper().strip(),
            "side": side.upper().strip(),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "position_size": float(position_size),
            "gross_pnl": gross_pnl,
            "fees": float(fees),
            "net_pnl": trade_record["pnl"],
            "current_capital": self.session.current_capital,
            "trade_record": trade_record,
            "timestamp": self._now(),
        }
