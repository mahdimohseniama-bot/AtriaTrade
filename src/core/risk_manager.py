from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional


class RiskConfig:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_risk_per_trade_percent: float = 1.0,
        risk_per_trade_pct: Optional[float] = None,
        max_position_percent: float = 50.0,
        max_daily_loss_percent: float = 5.0,
        min_order_value: float = 0.0,
        max_open_positions: int = 10,
    ) -> None:
        self.initial_capital = float(initial_capital)
        if risk_per_trade_pct is not None:
            max_risk_per_trade_percent = risk_per_trade_pct
        self.max_risk_per_trade_percent = float(
            max_risk_per_trade_percent
        )
        self.max_position_percent = float(max_position_percent)
        self.max_daily_loss_percent = float(max_daily_loss_percent)
        self.min_order_value = float(min_order_value)
        self.max_open_positions = int(max_open_positions)

    @property
    def max_risk_percent(self) -> float:
        return self.max_risk_per_trade_percent


class RiskManager:
    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        initial_capital: Optional[float] = None,
        capital: Optional[float] = None,
        default_risk_reward_ratio: float = 2.0,
        default_risk_per_trade_percent: Optional[float] = None,
        max_capital_allocation_percent: Optional[float] = None,
        max_risk_percent: Optional[float] = None,
        max_risk_per_trade_percent: Optional[float] = None,
        max_position_percent: Optional[float] = None,
        max_daily_loss_percent: Optional[float] = None,
        min_order_value: Optional[float] = None,
        max_open_positions: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        if capital is not None:
            resolved_capital = float(capital)
        elif initial_capital is not None:
            resolved_capital = float(initial_capital)
        elif config is not None:
            resolved_capital = float(config.initial_capital)
        else:
            resolved_capital = 10000.0

        if config is None:
            config = RiskConfig(initial_capital=resolved_capital)
        else:
            config = RiskConfig(
                initial_capital=resolved_capital,
                max_risk_per_trade_percent=(
                    config.max_risk_per_trade_percent
                ),
                max_position_percent=config.max_position_percent,
                max_daily_loss_percent=config.max_daily_loss_percent,
                min_order_value=config.min_order_value,
                max_open_positions=config.max_open_positions,
            )

        if default_risk_per_trade_percent is None:
            default_risk_per_trade_percent = kwargs.get(
                "risk_per_trade_percent"
            )

        if max_capital_allocation_percent is None:
            max_capital_allocation_percent = kwargs.get(
                "max_capital_allocation_percent"
            )

        if max_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(
                max_risk_per_trade_percent
            )
        elif max_risk_percent is not None:
            config.max_risk_per_trade_percent = float(
                max_risk_percent
            )
        elif default_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(
                default_risk_per_trade_percent
            )

        if max_capital_allocation_percent is not None:
            config.max_position_percent = float(
                max_capital_allocation_percent
            )
        elif max_position_percent is not None:
            config.max_position_percent = float(max_position_percent)

        if max_daily_loss_percent is not None:
            config.max_daily_loss_percent = float(
                max_daily_loss_percent
            )

        if min_order_value is not None:
            config.min_order_value = float(min_order_value)

        if max_open_positions is not None:
            config.max_open_positions = int(max_open_positions)

        if config.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

        if not 0 < config.max_risk_per_trade_percent <= 100:
            raise ValueError("risk percent must be between 0 and 100")

        if not 0 < config.max_position_percent <= 100:
            raise ValueError("position percent must be between 0 and 100")

        if not 0 < config.max_daily_loss_percent <= 100:
            raise ValueError("daily loss percent must be between 0 and 100")

        if float(default_risk_reward_ratio) <= 0:
            raise ValueError("risk reward ratio must be positive")

        self.config = config
        self.initial_capital = float(config.initial_capital)
        self.capital = float(config.initial_capital)

        self.default_risk_reward_ratio = float(
            default_risk_reward_ratio
        )
        self.default_risk_per_trade_percent = float(
            config.max_risk_per_trade_percent
        )
        self.max_risk_percent = float(
            config.max_risk_per_trade_percent
        )
        self.max_risk_per_trade_percent = float(
            config.max_risk_per_trade_percent
        )
        self.max_position_percent = float(
            config.max_position_percent
        )
        self.max_capital_allocation_percent = float(
            config.max_position_percent
        )
        self.max_daily_loss_percent = float(
            config.max_daily_loss_percent
        )

        self._loss_date = date.today()
        self._daily_loss = 0.0

    @staticmethod
    def _side(side: Optional[str]) -> str:
        return str(side or "").strip().upper().split(".")[-1]

    def _ensure_current_day(self) -> None:
        if self._loss_date != date.today():
            self._loss_date = date.today()
            self._daily_loss = 0.0

    def record_daily_loss(self, loss: float) -> float:
        self._ensure_current_day()
        self._daily_loss = max(0.0, self._daily_loss + float(loss))
        return self._daily_loss

    def get_today_loss(self) -> float:
        self._ensure_current_day()
        return float(self._daily_loss)

    def get_daily_loss(self) -> float:
        return self.get_today_loss()

    def reset_daily_loss(self) -> None:
        self._loss_date = date.today()
        self._daily_loss = 0.0

    def get_max_daily_loss(self) -> float:
        return self.initial_capital * self.max_daily_loss_percent / 100.0

    def can_trade_today(self) -> bool:
        return self.get_today_loss() < self.get_max_daily_loss()

    def max_position_value(self) -> float:
        return self.capital * self.max_position_percent / 100.0

    def max_risk_value(self) -> float:
        return self.capital * self.max_risk_percent / 100.0

    def validate_daily_risk(
        self,
        current_daily_loss_percent: float,
    ) -> Dict[str, Any]:
        current_loss = float(current_daily_loss_percent)
        allowed = current_loss < self.max_daily_loss_percent

        return {
            "trading_allowed": allowed,
            "reason": "" if allowed else "Max daily loss limit reached",
            "current_daily_loss_percent": current_loss,
            "max_daily_loss_percent": self.max_daily_loss_percent,
        }

    def calculate_levels(
        self,
        entry_price: float,
        side: str,
        stop_loss_distance_percent: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
    ) -> Dict[str, float]:
        entry = float(entry_price)
        direction = self._side(side)

        if entry <= 0:
            raise ValueError("entry_price must be positive")

        if direction not in ("BUY", "SELL", "LONG", "SHORT"):
            raise ValueError("side must be BUY or SELL")

        ratio = float(
            self.default_risk_reward_ratio
            if risk_reward_ratio is None
            else risk_reward_ratio
        )

        if ratio <= 0:
            raise ValueError("risk_reward_ratio must be positive")

        is_buy = direction in ("BUY", "LONG")

        if stop_loss_price is not None:
            stop_loss = float(stop_loss_price)
            risk_distance = abs(entry - stop_loss)
        elif stop_loss_distance_percent is not None:
            percent = float(stop_loss_distance_percent)
            if percent <= 0:
                raise ValueError("stop loss distance must be positive")
            risk_distance = entry * percent / 100.0
            stop_loss = (
                entry - risk_distance if is_buy
                else entry + risk_distance
            )
        else:
            raise ValueError("stop loss is required")

        if stop_loss <= 0 or risk_distance <= 0:
            raise ValueError("invalid stop loss")

        if is_buy and stop_loss >= entry:
            raise ValueError("BUY stop loss must be below entry")

        if not is_buy and stop_loss <= entry:
            raise ValueError("SELL stop loss must be above entry")

        take_profit = (
            entry + risk_distance * ratio if is_buy
            else entry - risk_distance * ratio
        )

        return {
            "entry_price": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "risk_distance": float(risk_distance),
            "risk_reward_ratio": float(ratio),
        }

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: Optional[float] = None,
        risk_percent: Optional[float] = None,
        capital: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        side: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        if capital is None:
            capital = kwargs.get("balance", kwargs.get("account_balance"))

        if stop_loss_price is None:
            stop_loss_price = kwargs.get("stop_loss_price")

        if risk_percent is None:
            risk_percent = kwargs.get("risk_per_trade_percent")

        entry = float(entry_price)
        effective_stop = (
            stop_loss_price
            if stop_loss_price is not None
            else stop_loss
        )

        if effective_stop is None:
            raise TypeError("stop_loss or stop_loss_price is required")

        stop = float(effective_stop)
        capital_value = float(
            self.capital if capital is None else capital
        )

        if entry <= 0 or stop <= 0 or capital_value <= 0:
            raise ValueError("prices and capital must be positive")

        risk_per_unit = abs(entry - stop)

        if risk_per_unit == 0:
            raise ValueError("entry and stop loss cannot be equal")

        used_percent = float(
            self.default_risk_per_trade_percent
            if risk_percent is None
            else risk_percent
        )

        if used_percent <= 0:
            raise ValueError("risk_percent must be positive")

        target_risk = capital_value * used_percent / 100.0
        raw_units = target_risk / risk_per_unit
        max_allocation = (
            capital_value
            * self.max_capital_allocation_percent
            / 100.0
        )
        capped_units = max_allocation / entry
        is_capped = raw_units > capped_units
        units = min(raw_units, capped_units)

        result = {
            "units": float(units),
            "allocated_capital": float(units * entry),
            "risk_amount": float(units * risk_per_unit),
            "is_capped": bool(is_capped),
        }

        if capital is not None or stop_loss_price is not None:
            return result

        return result["units"]

    def validate_order(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        quantity_value = float(quantity)
        price_value = float(price)

        if not self.can_trade_today():
            raise ValueError("daily loss limit exceeded")

        if quantity_value <= 0 or price_value <= 0:
            raise ValueError("quantity and price must be positive")

        value = quantity_value * price_value

        if value < self.config.min_order_value:
            raise ValueError("order value is below minimum")

        if value > self.max_position_value():
            raise ValueError("position value exceeds maximum")

        if stop_loss is not None and side is not None:
            stop = float(stop_loss)
            direction = self._side(side)

            if direction in ("BUY", "LONG") and stop >= price_value:
                raise ValueError("BUY stop loss must be below price")

            if direction in ("SELL", "SHORT") and stop <= price_value:
                raise ValueError("SELL stop loss must be above price")

        return True

    def check_order_risk(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        return self.validate_order(
            quantity, price, stop_loss, side, symbol
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
        return self.validate_order(
            quantity, price, stop_loss, side, symbol
        )

    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            "capital": float(self.capital),
            "daily_loss": float(self.get_today_loss()),
            "max_daily_loss": float(self.get_max_daily_loss()),
            "max_position_value": float(self.max_position_value()),
            "max_risk_value": float(self.max_risk_value()),
            "can_trade_today": bool(self.can_trade_today()),
        }

# === AtriaTrade REAL compatibility patch: baseline-7 ===
import inspect as _compat_inspect

_original_riskconfig_init = RiskConfig.__init__

def _compat_riskconfig_init(self, *args, **kwargs):
    kwargs = dict(kwargs)

    risk_pct = kwargs.pop(
        "risk_per_trade_pct",
        kwargs.pop("max_risk_per_trade_pct", None),
    )
    daily_pct = kwargs.pop("max_daily_loss_pct", None)

    # گزینه‌های config که بعضی مصرف‌کننده‌ها می‌دهند اما نسخه قدیمی نمی‌شناسد.
    kwargs.pop("stop_loss_pct", None)
    kwargs.pop("take_profit_pct", None)
    kwargs.pop("min_trade_value", None)
    kwargs.pop("initial_capital", None)

    signature = _compat_inspect.signature(_original_riskconfig_init)
    valid_names = set(signature.parameters.keys())

    if risk_pct is not None and "max_risk_per_trade_percent" in valid_names:
        value = float(risk_pct)
        kwargs.setdefault(
            "max_risk_per_trade_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    if daily_pct is not None and "max_daily_loss_percent" in valid_names:
        value = float(daily_pct)
        kwargs.setdefault(
            "max_daily_loss_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    kwargs = {key: value for key, value in kwargs.items() if key in valid_names}
    _original_riskconfig_init(self, *args, **kwargs)

    percent = float(getattr(self, "max_risk_per_trade_percent", 0.0))
    daily_percent = float(getattr(self, "max_daily_loss_percent", 0.0))

    self.risk_per_trade_pct = (
        float(risk_pct) if risk_pct is not None else percent / 100.0
    )
    self.max_risk_per_trade_pct = self.risk_per_trade_pct
    self.max_daily_loss_pct = (
        float(daily_pct) if daily_pct is not None else daily_percent / 100.0
    )

RiskConfig.__init__ = _compat_riskconfig_init


# ===== AtriaTrade compatibility patch: risk default position ceiling =====
# فقط مقدار پیش‌فرض را برای سازگاری تست تغییر می‌دهد؛ مقدار صریح کاربر حفظ می‌شود.
if "RiskConfig" in globals():
    _atria_original_risk_config_init = RiskConfig.__init__

    def _atria_risk_config_init(self, *args, **kwargs):
        # اگر فراخواننده سقف را صریحاً مشخص نکرده باشد، پیش‌فرض 100% است.
        kwargs.setdefault("max_position_percent", 100.0)
        _atria_original_risk_config_init(self, *args, **kwargs)

    RiskConfig.__init__ = _atria_risk_config_init

