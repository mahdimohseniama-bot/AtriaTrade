import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.capital_manager import CapitalManager
from src.core.risk_manager import RiskConfig, RiskManager
from src.core.trader_engine import TraderEngine


class PaperSession:
    """
    مدیریت یک نشست Paper Trading با استفاده از TraderEngine واقعی پروژه.

    این کلاس:
    - معاملات مجازی را باز و بسته می‌کند
    - تاریخچه معاملات را در JSON ذخیره می‌کند
    - سود و زیان معاملات را ثبت می‌کند
    - آمار نشست و Win Rate را محاسبه می‌کند
    """

    def __init__(
        self,
        session_name: str = "default_session",
        initial_capital: float = 10000.0,
        risk_config: Optional[RiskConfig] = None,
        data_dir: str = "data/paper_trades",
    ):
        if not session_name or not isinstance(session_name, str):
            raise ValueError("session_name must be a non-empty string")

        if initial_capital <= 0:
            raise ValueError("initial_capital must be greater than zero")

        self.session_name = session_name
        self.data_dir = data_dir
        self.session_file = os.path.join(
            self.data_dir,
            f"{self.session_name}.json",
        )

        os.makedirs(self.data_dir, exist_ok=True)

        self.capital_manager = CapitalManager(
            initial_capital=float(initial_capital)
        )

        self.risk_manager = RiskManager(
            config=risk_config
        )

        # نام پارامترها مطابق API واقعی TraderEngine است.
        self.engine = TraderEngine(
            capital_manager=self.capital_manager,
            risk_manager=self.risk_manager,
        )

        self.history: List[Dict[str, Any]] = []

    @staticmethod
    def _utc_now() -> str:
        """برگرداندن زمان فعلی به‌صورت UTC و قابل ذخیره در JSON."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read_value(
        obj: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        خواندن مقدار از dict یا object.

        TraderEngine در این پروژه برای Position یک object برمی‌گرداند،
        ولی این تابع برای سازگاری با خروجی‌های dict نیز آماده است.
        """
        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    @staticmethod
    def _to_json_safe(value: Any) -> Any:
        """
        تبدیل objectهای پروژه به ساختاری قابل ذخیره در JSON.
        """
        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, dict):
            return {
                str(key): PaperSession._to_json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                PaperSession._to_json_safe(item)
                for item in value
            ]

        if hasattr(value, "__dict__"):
            return {
                str(key): PaperSession._to_json_safe(item)
                for key, item in vars(value).items()
            }

        return str(value)

    @staticmethod
    def _is_successful_open(result: Any) -> bool:
        """
        تشخیص موفقیت بازشدن معامله.

        در TraderEngine فعلی، خروجی Position است.
        برای سازگاری، dict و bool نیز پشتیبانی می‌شوند.
        """
        if result is None:
            return False

        if isinstance(result, dict):
            if "success" in result:
                return bool(result["success"])

            status = str(result.get("status", "")).upper()
            if status in {"REJECTED", "FAILED", "ERROR"}:
                return False

            return True

        if isinstance(result, bool):
            return result

        status = str(
            getattr(result, "status", "OPEN")
        ).upper()

        return status not in {"REJECTED", "FAILED", "ERROR"}

    @staticmethod
    def _extract_pnl(result: Any) -> Optional[float]:
        """
        استخراج PNL از خروجی close_virtual_position.

        در API واقعی، خروجی Position است و pnl به‌صورت attribute
        داخل آن قرار دارد.
        """
        pnl = PaperSession._read_value(result, "pnl")

        if pnl is None and isinstance(result, dict):
            for key in (
                "profit",
                "realized_pnl",
                "realized_profit",
            ):
                if result.get(key) is not None:
                    pnl = result[key]
                    break

        if pnl is None:
            return None

        try:
            return float(pnl)
        except (TypeError, ValueError):
            return None

    def execute_paper_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
    ) -> Dict[str, Any]:
        """
        اجرای کامل یک معامله مجازی.

        بازکردن:
            open_virtual_position(
                symbol=symbol,
                side=side,
                current_price=entry_price
            )

        بستن:
            close_virtual_position(
                symbol=symbol,
                exit_price=exit_price
            )
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol must be a non-empty string")

        if side not in {"buy", "sell"}:
            raise ValueError("side must be either 'buy' or 'sell'")

        if entry_price <= 0 or exit_price <= 0:
            raise ValueError("entry_price and exit_price must be positive")

        print(
            f"Executing paper trade: "
            f"{symbol} {entry_price:,.2f} -> {exit_price:,.2f}"
        )

        # بازکردن معامله با API واقعی TraderEngine
        open_result = self.engine.open_virtual_position(
            symbol=symbol,
            side=side,
            current_price=float(entry_price),
        )

        if not self._is_successful_open(open_result):
            record = {
                "timestamp": self._utc_now(),
                "symbol": symbol,
                "side": side,
                "status": "REJECTED",
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "pnl": 0.0,
                "reason": self._read_value(
                    open_result,
                    "reason",
                    "Virtual position was rejected",
                ),
            }

            self.history.append(record)
            self._save_session()
            return record

        # بستن معامله با API واقعی TraderEngine
        close_result = self.engine.close_virtual_position(
            symbol=symbol,
            exit_price=float(exit_price),
        )

        pnl = self._extract_pnl(close_result)

        # در حالت عادی pnl باید از Position خوانده شود.
        # اگر API مقدار None برگرداند، برای جلوگیری از ثبت اشتباه،
        # وضعیت معامله را CLOSED ولی مقدار pnl را None نگه می‌داریم.
        record = {
            "timestamp": self._utc_now(),
            "symbol": symbol,
            "side": side,
            "status": str(
                self._read_value(
                    close_result,
                    "status",
                    "CLOSED",
                )
            ).upper(),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "pnl": pnl,
            "position": self._to_json_safe(close_result),
            "portfolio_summary": self._to_json_safe(
                self.engine.get_portfolio_summary()
            ),
        }

        self.history.append(record)
        self._save_session()

        return record

    def _save_session(self) -> None:
        """ذخیره نشست و معاملات در فایل JSON."""
        data = {
            "session_name": self.session_name,
            "last_updated": self._utc_now(),
            "summary": self._to_json_safe(
                self.engine.get_portfolio_summary()
            ),
            "total_trades": len(self.history),
            "trades": self._to_json_safe(self.history),
        }

        with open(
            self.session_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )

    def get_session_stats(self) -> Dict[str, Any]:
        """محاسبه آمار معاملات بسته‌شده نشست."""
        summary = self.engine.get_portfolio_summary()

        closed_trades = [
            trade
            for trade in self.history
            if trade.get("status") == "CLOSED"
        ]

        winning_trades = [
            trade
            for trade in closed_trades
            if isinstance(trade.get("pnl"), (int, float))
            and trade["pnl"] > 0
        ]

        losing_trades = [
            trade
            for trade in closed_trades
            if isinstance(trade.get("pnl"), (int, float))
            and trade["pnl"] < 0
        ]

        total_closed = len(closed_trades)

        win_rate = (
            len(winning_trades) / total_closed * 100
            if total_closed > 0
            else 0.0
        )

        total_pnl = sum(
            float(trade["pnl"])
            for trade in closed_trades
            if isinstance(trade.get("pnl"), (int, float))
        )

        return {
            "session_name": self.session_name,
            "total_trades": total_closed,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_pct": round(win_rate, 2),
            "total_pnl": round(total_pnl, 8),
            "portfolio": self._to_json_safe(summary),
        }
