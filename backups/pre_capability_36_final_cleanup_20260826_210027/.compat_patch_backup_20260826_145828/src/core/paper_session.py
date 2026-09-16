from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class PaperSession:
    """
    نشست معاملات آزمایشی.

    این کلاس:
    - سرمایه اولیه و فعلی را نگهداری می‌کند.
    - معاملات انجام‌شده را ثبت می‌کند.
    - سود و زیان را روی سرمایه اعمال می‌کند.
    - امکان ذخیره و بارگذاری JSON دارد.
    """

    def __init__(
        self,
        session_name: str,
        initial_capital: float,
        currency: str = "USDT",
        session_id: Optional[str] = None,
    ) -> None:
        if not isinstance(session_name, str) or not session_name.strip():
            raise ValueError("نام نشست نمی‌تواند خالی باشد.")

        if initial_capital <= 0:
            raise ValueError("سرمایه اولیه باید بزرگ‌تر از صفر باشد.")

        self.session_name = session_name.strip()
        self.session_id = session_id or self.session_name
        self.currency = currency.upper()

        self.initial_capital = float(initial_capital)
        self.current_capital = float(initial_capital)
        self.total_pnl = 0.0

        self.trades: List[Dict[str, Any]] = []
        self.created_at = self._now()
        self.updated_at = self.created_at

        # برای سازگاری با کدهای قبلی
        self.capital_manager = self

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @property
    def balance(self) -> float:
        """موجودی فعلی نشست."""
        return self.current_capital

    def update_capital_after_trade(self, pnl: float) -> float:
        """
        اعمال سود یا زیان معامله روی سرمایه.
        """
        pnl = float(pnl)
        self.total_pnl += pnl
        self.current_capital += pnl
        self.updated_at = self._now()
        return self.current_capital

    def record_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        size: float,
        pnl: float,
        leverage: float = 1.0,
        fees: float = 0.0,
    ) -> Dict[str, Any]:
        """
        ثبت کامل یک معامله بسته‌شده.
        """

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("نماد معامله نمی‌تواند خالی باشد.")

        if entry_price <= 0:
            raise ValueError("قیمت ورود باید بزرگ‌تر از صفر باشد.")

        if exit_price <= 0:
            raise ValueError("قیمت خروج باید بزرگ‌تر از صفر باشد.")

        if size <= 0:
            raise ValueError("حجم معامله باید بزرگ‌تر از صفر باشد.")

        if leverage <= 0:
            raise ValueError("اهرم باید بزرگ‌تر از صفر باشد.")

        if fees < 0:
            raise ValueError("کارمزد نمی‌تواند منفی باشد.")

        side = side.upper().strip()

        if side in ("BUY", "LONG"):
            normalized_side = "LONG"
        elif side in ("SELL", "SHORT"):
            normalized_side = "SHORT"
        else:
            raise ValueError("سمت معامله باید BUY، SELL، LONG یا SHORT باشد.")

        gross_pnl = float(pnl)
        net_pnl = gross_pnl - float(fees)

        trade_number = len(self.trades) + 1
        trade_id = f"{self.session_id}_TRADE_{trade_number:05d}"

        trade_record: Dict[str, Any] = {
            "trade_id": trade_id,
            "symbol": symbol.strip().upper(),
            "side": normalized_side,
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "size": float(size),
            "leverage": float(leverage),
            "gross_pnl": gross_pnl,
            "fees": float(fees),
            "pnl": net_pnl,
            "currency": self.currency,
            "timestamp": self._now(),
        }

        self.trades.append(trade_record)
        self.update_capital_after_trade(net_pnl)

        return trade_record

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل نشست به دیکشنری قابل ذخیره در JSON.
        """
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "currency": self.currency,
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_pnl": self.total_pnl,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "trades": self.trades,
        }

    def save(self, file_path: str | Path) -> Path:
        """
        ذخیره نشست در فایل JSON.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return path

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperSession":
        """
        ساخت نشست از دیکشنری.
        """
        session = cls(
            session_name=data["session_name"],
            initial_capital=float(data["initial_capital"]),
            currency=data.get("currency", "USDT"),
            session_id=data.get("session_id"),
        )

        session.current_capital = float(
            data.get("current_capital", session.initial_capital)
        )
        session.total_pnl = float(data.get("total_pnl", 0.0))
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.trades = list(data.get("trades", []))

        return session

    @classmethod
    def load(cls, file_path: str | Path) -> "PaperSession":
        """
        بارگذاری نشست از فایل JSON.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"فایل نشست پیدا نشد: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def summary(self) -> Dict[str, Any]:
        """
        خلاصه وضعیت نشست.
        """
        winning_trades = sum(1 for trade in self.trades if trade["pnl"] > 0)
        losing_trades = sum(1 for trade in self.trades if trade["pnl"] < 0)

        return {
            "session_name": self.session_name,
            "currency": self.currency,
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_pnl": self.total_pnl,
            "trade_count": len(self.trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
        }

    def __repr__(self) -> str:
        return (
            f"PaperSession("
            f"name={self.session_name!r}, "
            f"capital={self.current_capital:.2f}, "
            f"trades={len(self.trades)})"
        )
