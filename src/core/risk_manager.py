"""AtriaTrade - Risk Management

این ماژول فقط برای Paper Trading، Backtesting و Testnet طراحی شده است.
هیچ اتصال یا اجرای معامله واقعی در این فایل وجود ندارد.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class RiskConfig:
    """تنظیمات مدیریت ریسک."""

    initial_capital: float = 10_000.0
    max_risk_per_trade_percent: float = 1.0
    max_position_percent: float = 50.0
    max_daily_loss_percent: float = 5.0
    min_order_value: float = 0.0
    max_open_positions: int = 10

    @property
    def max_risk_percent(self) -> float:
        """نام جایگزین برای سازگاری با تست‌ها و نسخه‌های قبلی."""
        return self.max_risk_per_trade_percent


class RiskManager:
    """مدیریت محدودیت‌های ریسک سفارش و زیان روزانه."""

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        initial_capital: Optional[float] = None,
        capital: Optional[float] = None,
        max_risk_percent: Optional[float] = None,
        max_risk_per_trade_percent: Optional[float] = None,
        max_position_percent: Optional[float] = None,
        max_daily_loss_percent: Optional[float] = None,
        min_order_value: Optional[float] = None,
        max_open_positions: Optional[int] = None,
        **kwargs: Any,
    ):
        # اولویت سرمایه:
        # capital از تست فعلی، سپس initial_capital، سپس config
        if capital is not None:
            resolved_capital = float(capital)
        elif initial_capital is not None:
            resolved_capital = float(initial_capital)
        elif config is not None:
            resolved_capital = float(config.initial_capital)
        else:
            resolved_capital = 10_000.0

        if config is None:
            config = RiskConfig(initial_capital=resolved_capital)
        else:
            # یک کپی مستقل می‌سازیم تا تنظیمات بیرونی ناخواسته تغییر نکند.
            config = RiskConfig(
                initial_capital=resolved_capital,
                max_risk_per_trade_percent=float(
                    config.max_risk_per_trade_percent
                ),
                max_position_percent=float(config.max_position_percent),
                max_daily_loss_percent=float(config.max_daily_loss_percent),
                min_order_value=float(config.min_order_value),
                max_open_positions=int(config.max_open_positions),
            )

        if max_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(
                max_risk_per_trade_percent
            )
        elif max_risk_percent is not None:
            config.max_risk_per_trade_percent = float(max_risk_percent)

        if max_position_percent is not None:
            config.max_position_percent = float(max_position_percent)

        if max_daily_loss_percent is not None:
            config.max_daily_loss_percent = float(max_daily_loss_percent)

        if min_order_value is not None:
            config.min_order_value = float(min_order_value)

        if max_open_positions is not None:
            config.max_open_positions = int(max_open_positions)

        if config.initial_capital <= 0:
            raise ValueError("initial capital must be greater than zero")

        if not 0 < config.max_risk_per_trade_percent <= 100:
            raise ValueError("max risk percent must be between 0 and 100")

        if not 0 < config.max_position_percent <= 100:
            raise ValueError(
                "max position percent must be between 0 and 100"
            )

        if not 0 < config.max_daily_loss_percent <= 100:
            raise ValueError(
                "max daily loss percent must be between 0 and 100"
            )

        self.config = config

        # نام‌های سازگار با کدهای مختلف پروژه
        self.initial_capital = config.initial_capital
        self.capital = config.initial_capital
        self.max_risk_percent = config.max_risk_per_trade_percent
        self.max_risk_per_trade_percent = (
            config.max_risk_per_trade_percent
        )
        self.max_position_percent = config.max_position_percent
        self.max_daily_loss_percent = config.max_daily_loss_percent

        self._loss_date: date = date.today()
        self._daily_loss: float = 0.0

    # ------------------------------------------------------------------
    # Daily loss management
    # ------------------------------------------------------------------

    def _ensure_current_day(self) -> None:
        """در روز جدید، زیان روزانه را از صفر شروع می‌کند."""
        today = date.today()
        if today != self._loss_date:
            self._loss_date = today
            self._daily_loss = 0.0

    def record_daily_loss(self, loss: float) -> float:
        """ثبت زیان روزانه.

        مقدار مثبت یا منفی پذیرفته می‌شود؛ مقدار نهایی زیان هیچ‌گاه منفی
        نمی‌شود.
        """
        self._ensure_current_day()

        value = float(loss)

        # اگر سود ثبت شود، زیان روزانه کاهش می‌یابد اما منفی نمی‌شود.
        self._daily_loss = max(0.0, self._daily_loss + value)
        return self._daily_loss

    def get_today_loss(self) -> float:
        """برگرداندن زیان ثبت‌شده امروز."""
        self._ensure_current_day()
        return float(self._daily_loss)

    def get_daily_loss(self) -> float:
        """نام جایگزین برای get_today_loss."""
        return self.get_today_loss()

    def get_max_daily_loss(self) -> float:
        """حداکثر زیان مجاز روزانه بر اساس سرمایه اولیه."""
        return (
            self.initial_capital
            * self.max_daily_loss_percent
            / 100.0
        )

    def can_trade_today(self) -> bool:
        """بررسی امکان معامله در روز جاری."""
        return self.get_today_loss() < self.get_max_daily_loss()

    def reset_daily_loss(self) -> None:
        """صفرکردن زیان روزانه."""
        self._loss_date = date.today()
        self._daily_loss = 0.0

    # ------------------------------------------------------------------
    # Position and order risk checks
    # ------------------------------------------------------------------

    def max_position_value(self) -> float:
        """حداکثر ارزش مجاز یک پوزیشن."""
        return self.capital * self.max_position_percent / 100.0

    def max_risk_value(self) -> float:
        """حداکثر ریسک مجاز هر معامله."""
        return self.capital * self.max_risk_percent / 100.0

    def validate_order(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        """اعتبارسنجی عمومی سفارش."""

        if not self.can_trade_today():
            raise ValueError("daily loss limit exceeded")

        quantity = float(quantity)
        price = float(price)

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if price <= 0:
            raise ValueError("price must be greater than zero")

        position_value = quantity * price

        if position_value < self.config.min_order_value:
            raise ValueError("order value is below minimum order value")

        if position_value > self.max_position_value():
            raise ValueError("position value exceeds maximum allowed limit")

        if stop_loss is not None:
            stop_loss = float(stop_loss)

            if stop_loss <= 0:
                raise ValueError("stop_loss must be greater than zero")

            normalized_side = str(side or "").upper()
            normalized_side = normalized_side.split(".")[-1]

            if normalized_side in {"BUY", "LONG"}:
                if stop_loss >= price:
                    raise ValueError(
                        "for BUY orders stop_loss must be below price"
                    )

            elif normalized_side in {"SELL", "SHORT"}:
                if stop_loss <= price:
                    raise ValueError(
                        "for SELL orders stop_loss must be above price"
                    )

        return True

    def check_order_risk(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        """نام جایگزین برای validate_order."""
        return self.validate_order(
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            side=side,
            symbol=symbol,
        )

    def can_open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """بررسی امکان بازکردن پوزیشن."""
        return self.validate_order(
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            side=side,
            symbol=symbol,
        )

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_percent: Optional[float] = None,
    ) -> float:
        """محاسبه حجم پوزیشن بر اساس فاصله حد ضرر."""

        entry_price = float(entry_price)
        stop_loss = float(stop_loss)

        if entry_price <= 0 or stop_loss <= 0:
            raise ValueError("prices must be greater than zero")

        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit <= 0:
            raise ValueError("entry price and stop loss cannot be equal")

        percent = (
            self.max_risk_percent
            if risk_percent is None
            else float(risk_percent)
        )

        risk_amount = self.capital * percent / 100.0
        quantity = risk_amount / risk_per_unit

        # حجم محاسبه‌شده نباید سقف ارزش پوزیشن را رد کند.
        maximum_quantity = self.max_position_value() / entry_price

        return max(0.0, min(quantity, maximum_quantity))

    def get_risk_summary(self) -> Dict[str, float]:
        """خلاصه وضعیت ریسک برای تست و داشبورد."""
        return {
            "capital": float(self.capital),
            "daily_loss": float(self.get_today_loss()),
            "max_daily_loss": float(self.get_max_daily_loss()),
            "max_position_value": float(self.max_position_value()),
            "max_risk_value": float(self.max_risk_value()),
            "can_trade_today": self.can_trade_today(),
        }
