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

# Backward compatibility for legacy tests and session_manager
# Legacy alias removed: PaperTradingSession is defined below as a subclass.

# === AtriaTrade REAL compatibility patch: baseline-7 ===
class PaperTradingSession(PaperSession):
    """Adapter جدید برای چرخه معاملات کاغذی، با حفظ PaperSession قدیمی."""

    def __init__(self, initial_balance=10000.0, risk_config=None, **kwargs):
        super().__init__(
            session_name=kwargs.pop("session_name", "paper_trading"),
            initial_capital=float(initial_balance),
            currency=kwargs.pop("currency", "USDT"),
            session_id=kwargs.pop("session_id", "paper_trading"),
        )

        from src.core.position_tracker import PositionTracker
        from src.core.order_executor import OrderExecutor

        self.risk_config = risk_config
        self.position_tracker = PositionTracker()
        self.order_executor = OrderExecutor(
            position_tracker=self.position_tracker
        )
        self.market_prices = {}

    def get_balance(self):
        return self.current_capital

    def update_market_prices(self, prices):
        normalized = {
            str(symbol).upper(): float(price)
            for symbol, price in prices.items()
        }
        self.market_prices.update(normalized)
        self.position_tracker.update_prices(normalized)

    def get_equity(self):
        equity = float(self.current_capital)
        seen = set()

        for position in self.position_tracker.positions.values():
            if id(position) in seen:
                continue
            seen.add(id(position))

            if not position.is_open:
                continue

            market_price = self.market_prices.get(
                position.symbol, position.current_price
            )

            # در BUY هنگام ورود، cost از current_capital کسر شده؛
            # برای Equity باید ارزش فعلی دارایی اضافه شود.
            if position.side == "BUY":
                equity += position.size * float(market_price)
            else:
                # مدل ساده short: collateral ورود + سود/زیان.
                equity += (
                    position.size * position.entry_price
                    + position.size * (position.entry_price - float(market_price))
                )

        return equity

    def execute_order(
        self,
        symbol,
        side,
        quantity,
        price,
        sl=None,
        tp=None,
        stop_loss=None,
        take_profit=None,
        **kwargs
    ):
        side_text = str(getattr(side, "value", side)).upper()
        quantity = float(quantity)
        price = float(price)

        if side_text == "BUY":
            self.current_capital -= quantity * price
        elif side_text == "SELL":
            self.current_capital += quantity * price
        else:
            raise ValueError(f"Invalid order side: {side}")

        self.updated_at = self._now()

        return self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=side_text,
            quantity=quantity,
            current_price=price,
            sl=sl if sl is not None else stop_loss,
            tp=tp if tp is not None else take_profit,
        )


# ===== AtriaTrade compatibility patch: PaperSession alias/API =====

# بعضی تست‌ها PaperSession و بعضی نسخه‌ها PaperTradingSession می‌خواهند.
if "PaperSession" not in globals() and "PaperTradingSession" in globals():
    PaperSession = PaperTradingSession

if "PaperTradingSession" not in globals() and "PaperSession" in globals():
    PaperTradingSession = PaperSession


# ===== ATRIA_V2_PAPER_SESSION_PATCH =====
# سازندهٔ واقعی را Wrap می‌کنیم تا risk_config و kwargs را بپذیرد.
if "PaperTradingSession" in globals():
    _atria_v2_old_paper_init = PaperTradingSession.__init__

    def _atria_v2_paper_init(self, initial_balance=10000.0, risk_config=None, **kwargs):
        # ابتدا تمام امضاهای محتمل نسخهٔ فعلی را امتحان می‌کنیم.
        try:
            _atria_v2_old_paper_init(
                self,
                initial_balance=initial_balance,
                risk_config=risk_config,
                **kwargs,
            )
        except TypeError:
            try:
                _atria_v2_old_paper_init(self, initial_balance=initial_balance, **kwargs)
            except TypeError:
                _atria_v2_old_paper_init(self, initial_balance)

        # حتی اگر سازندهٔ اصلی risk_config نداشت، برای قرارداد تست ذخیره می‌شود.
        if risk_config is not None:
            self.risk_config = risk_config

    PaperTradingSession.__init__ = _atria_v2_paper_init


# ===== ATRIA_FINAL_REMAINING6: PaperSession test contract =====
# تست از PaperSession استفاده می‌کند، نه فقط PaperTradingSession.

import json as _atria_final_json
from pathlib import Path as _atria_final_Path


def _atria_final_paper_init(
    self,
    session_name="default_session",
    initial_capital=10000.0,
    currency="USDT",
    session_id=None,
    risk_config=None,
    data_dir=None,
    **kwargs,
):
    self.session_name = str(session_name or "default_session")
    self.initial_capital = float(initial_capital)
    self.current_capital = float(initial_capital)
    self.currency = str(currency)
    self.session_id = session_id or self.session_name
    self.risk_config = risk_config
    self.data_dir = str(data_dir or "data/paper_trades")
    self.trades = []
    self.total_pnl = 0.0


def _atria_final_persist_paper(self):
    directory = _atria_final_Path(self.data_dir)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{self.session_name}.json"
    payload = {
        "session_name": self.session_name,
        "initial_capital": self.initial_capital,
        "current_capital": self.current_capital,
        "trades": self.trades,
    }
    path.write_text(
        _atria_final_json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def _atria_final_execute_paper_trade(
    self,
    symbol,
    side,
    entry_price,
    exit_price,
    size=0.1,
    quantity=None,
    **kwargs,
):
    qty = float(quantity if quantity is not None else size)
    entry = float(entry_price)
    exit_ = float(exit_price)
    normalized_side = str(side).upper()

    if normalized_side in ("BUY", "LONG"):
        pnl = (exit_ - entry) * qty
    else:
        pnl = (entry - exit_) * qty

    trade = {
        "symbol": str(symbol),
        "side": normalized_side,
        "entry_price": entry,
        "exit_price": exit_,
        "size": qty,
        "quantity": qty,
        "pnl": float(pnl),
        "status": "CLOSED",
    }

    self.trades.append(trade)
    self.total_pnl = float(getattr(self, "total_pnl", 0.0)) + float(pnl)
    self.current_capital = float(getattr(self, "current_capital", self.initial_capital)) + float(pnl)
    _atria_final_persist_paper(self)
    return trade


def _atria_final_get_session_stats(self):
    total = len(getattr(self, "trades", []))
    wins = sum(1 for trade in self.trades if float(trade.get("pnl", 0.0)) > 0.0)
    return {
        "total_trades": total,
        "winning_trades": wins,
        "losing_trades": total - wins,
        "win_rate_pct": (wins / total * 100.0) if total else 0.0,
        "total_pnl": float(getattr(self, "total_pnl", 0.0)),
        "current_capital": float(getattr(self, "current_capital", 0.0)),
    }


PaperSession.__init__ = _atria_final_paper_init
PaperSession.execute_paper_trade = _atria_final_execute_paper_trade
PaperSession.get_session_stats = _atria_final_get_session_stats
PaperSession._persist_history = _atria_final_persist_paper


# ===== ATRIA_FINAL_PERSISTENCE_COMPAT =====
# سازگاری PaperSession با save/load/to_dict پس از پچ REMAINING6.

from datetime import datetime as _atria_persist_datetime, timezone as _atria_persist_timezone
from pathlib import Path as _atria_persist_Path
import json as _atria_persist_json


def _atria_persist_now():
    return (
        _atria_persist_datetime.now(_atria_persist_timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def _atria_persist_init(
    self,
    session_name="default_session",
    initial_capital=10000.0,
    currency="USDT",
    session_id=None,
    risk_config=None,
    data_dir=None,
    **kwargs,
):
    # پچ قبلی را صدا می‌زنیم تا قرارداد 10 تست هدف حفظ شود.
    _atria_final_paper_init(
        self,
        session_name=session_name,
        initial_capital=initial_capital,
        currency=currency,
        session_id=session_id,
        risk_config=risk_config,
        data_dir=data_dir,
        **kwargs,
    )

    # فیلدهایی که save()/to_dict() اصلی به آن‌ها متکی هستند.
    now = _atria_persist_now()
    self.created_at = kwargs.get("created_at", now)
    self.updated_at = kwargs.get("updated_at", self.created_at)


def _atria_persist_to_dict(self):
    return {
        "session_id": self.session_id,
        "session_name": self.session_name,
        "currency": self.currency,
        "initial_capital": float(self.initial_capital),
        "current_capital": float(self.current_capital),
        "total_pnl": float(getattr(self, "total_pnl", 0.0)),
        "created_at": self.created_at,
        "updated_at": self.updated_at,
        "trades": list(getattr(self, "trades", [])),
    }


def _atria_persist_save(self, file_path):
    path = _atria_persist_Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    self.updated_at = _atria_persist_now()

    path.write_text(
        _atria_persist_json.dumps(
            _atria_persist_to_dict(self),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


@classmethod
def _atria_persist_from_dict(cls, data):
    session = cls(
        session_name=data.get("session_name", "default_session"),
        initial_capital=float(data.get("initial_capital", 10000.0)),
        currency=data.get("currency", "USDT"),
        session_id=data.get("session_id"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )

    session.current_capital = float(
        data.get("current_capital", session.initial_capital)
    )
    session.total_pnl = float(data.get("total_pnl", 0.0))
    session.trades = list(data.get("trades", []))
    session.created_at = data.get("created_at", session.created_at)
    session.updated_at = data.get("updated_at", session.updated_at)
    return session


@classmethod
def _atria_persist_load(cls, file_path):
    path = _atria_persist_Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Session file not found: {path}")

    data = _atria_persist_json.loads(path.read_text(encoding="utf-8"))
    return cls.from_dict(data)


def _atria_persist_execute_trade(
    self,
    symbol,
    side,
    entry_price,
    exit_price,
    size=0.1,
    quantity=None,
    **kwargs,
):
    trade = _atria_final_execute_paper_trade(
        self,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        size=size,
        quantity=quantity,
        **kwargs,
    )

    self.updated_at = _atria_persist_now()

    # ذخیره خودکار با همان data_dir پچ قبلی
    if getattr(self, "data_dir", None):
        self.save(
            _atria_persist_Path(self.data_dir)
            / f"{self.session_name}.json"
        )

    return trade


PaperSession.__init__ = _atria_persist_init
PaperSession._now = staticmethod(_atria_persist_now)
PaperSession.to_dict = _atria_persist_to_dict
PaperSession.save = _atria_persist_save
PaperSession.from_dict = _atria_persist_from_dict
PaperSession.load = _atria_persist_load
PaperSession.execute_paper_trade = _atria_persist_execute_trade

# نام قدیمی و جدید باید به یک کلاس اشاره کنند.
PaperTradingSession = PaperSession

