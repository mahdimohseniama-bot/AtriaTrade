"""مدیریت ریسک — AtriaTrade"""
from __future__ import annotations

from datetime import date
from typing import Optional


class RiskManager:
    def __init__(
        self,
        capital: Optional[float] = None,
        initial_capital: Optional[float] = None,
        max_risk_percent: float = 1.0,
        max_position_percent: float = 20.0,
        max_daily_loss_percent: float = 5.0,
    ) -> None:
        if capital is None:
            capital = initial_capital if initial_capital is not None else 10000.0
        self._validate_positive(capital, "capital")
        self._validate_positive(max_risk_percent, "max_risk_percent")
        self._validate_positive(max_position_percent, "max_position_percent")
        self._validate_positive(max_daily_loss_percent, "max_daily_loss_percent")

        self.capital = float(capital)
        self.max_risk_percent = float(max_risk_percent)
        self.max_position_percent = float(max_position_percent)
        self.max_daily_loss_percent = float(max_daily_loss_percent)
        self._daily_loss: dict[str, float] = {}

    @staticmethod
    def _validate_positive(value, name: str) -> None:
        if value is None or not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{name} باید عددی بزرگ‌تر از صفر باشد")

    # ---------- محاسبات ----------
    def calculate_risk_amount(self) -> float:
        """حداکثر مبلغ ریسک مجاز برای هر معامله"""
        return self.capital * self.max_risk_percent / 100.0

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """حجم بر اساس ریسک: مبلغ ریسک تقسیم بر فاصله قیمت تا حد ضرر"""
        if entry_price is None or entry_price <= 0:
            raise ValueError("entry_price باید بزرگ‌تر از صفر باشد")
        if stop_loss is None or stop_loss <= 0:
            raise ValueError("stop_loss باید بزرگ‌تر از صفر باشد")
        distance = abs(entry_price - stop_loss)
        if distance <= 0:
            raise ValueError("فاصله Entry تا Stop Loss باید بزرگ‌تر از صفر باشد")
        return self.calculate_risk_amount() / distance

    def calculate_position_value(self, quantity: float, entry_price: float) -> float:
        if quantity is None or quantity <= 0 or entry_price is None or entry_price <= 0:
            raise ValueError("quantity و entry_price باید بزرگ‌تر از صفر باشند")
        return quantity * entry_price

    def calculate_max_position_value(self) -> float:
        return self.capital * self.max_position_percent / 100.0

    # ---------- اعتبارسنجی ریسک معامله ----------
    def validate_trade_risk(
        self,
        symbol: str,
        side,
        entry_price: float,
        stop_loss: float,
        quantity: float,
    ) -> dict:
        if hasattr(side, "value"):
            side = str(side.value).upper()
        else:
            side = str(side).upper()
        if side not in ("BUY", "SELL"):
            return {"allowed": False, "reason": "سمت نامعتبر است", "symbol": symbol}

        if entry_price is None or entry_price <= 0:
            return {"allowed": False, "reason": "قیمت ورود نامعتبر است", "symbol": symbol}
        if stop_loss is None or stop_loss <= 0:
            return {"allowed": False, "reason": "حد ضرر نامعتبر است", "symbol": symbol}
        if quantity is None or quantity <= 0:
            return {"allowed": False, "reason": "حجم نامعتبر است", "symbol": symbol}

        # جهت حد ضرر
        if side == "BUY" and stop_loss >= entry_price:
            return {"allowed": False, "reason": "در BUY حد ضرر باید پایین‌تر از قیمت ورود باشد", "symbol": symbol}
        if side == "SELL" and stop_loss <= entry_price:
            return {"allowed": False, "reason": "در SELL حد ضرر باید بالاتر از قیمت ورود باشد", "symbol": symbol}

        # حداکثر ریسک هر معامله
        risk_amount = abs(entry_price - stop_loss) * quantity
        max_risk = self.calculate_risk_amount()
        if risk_amount > max_risk + 1e-9:
            return {
                "allowed": False,
                "reason": f"ریسک معامله {risk_amount:.2f} از سقف مجاز {max_risk:.2f} بیشتر است",
                "symbol": symbol,
                "risk_amount": risk_amount,
            }

        # حداکثر ارزش پوزیشن
        position_value = self.calculate_position_value(quantity, entry_price)
        max_position_value = self.calculate_max_position_value()
        if position_value > max_position_value + 1e-9:
            return {
                "allowed": False,
                "reason": f"ارزش پوزیشن {position_value:.2f} از سقف {max_position_value:.2f} بیشتر است",
                "symbol": symbol,
                "position_value": position_value,
            }

        # سقف ضرر روزانه
        if not self.can_trade_today():
            return {
                "allowed": False,
                "reason": "سقف ضرر روزانه تکمیل شده است",
                "symbol": symbol,
            }

        return {
            "allowed": True,
            "reason": "OK",
            "symbol": symbol,
            "risk_amount": risk_amount,
            "position_value": position_value,
            "max_position_value": max_position_value,
            "max_risk_amount": max_risk,
        }

    # ---------- ضرر روزانه ----------
    def _today(self) -> str:
        return date.today().isoformat()

    def record_daily_loss(self, amount: float) -> float:
        if amount is None or amount <= 0:
            raise ValueError("amount باید بزرگ‌تر از صفر باشد")
        today = self._today()
        self._daily_loss[today] = self._daily_loss.get(today, 0.0) + float(amount)
        return self._daily_loss[today]

    def get_today_loss(self) -> float:
        return self._daily_loss.get(self._today(), 0.0)

    def get_max_daily_loss_amount(self) -> float:
        return self.capital * self.max_daily_loss_percent / 100.0

    def can_trade_today(self) -> bool:
        return self.get_today_loss() < self.get_max_daily_loss_amount()

    def reset_daily_loss(self) -> None:
        self._daily_loss[self._today()] = 0.0

    # ---------- سرمایه ----------
    def update_capital(self, new_capital: float) -> None:
        self._validate_positive(new_capital, "new_capital")
        self.capital = float(new_capital)

    def get_status(self) -> dict:
        return {
            "capital": self.capital,
            "max_risk_percent": self.max_risk_percent,
            "max_risk_amount": self.calculate_risk_amount(),
            "max_position_percent": self.max_position_percent,
            "max_position_value": self.calculate_max_position_value(),
            "max_daily_loss_percent": self.max_daily_loss_percent,
            "max_daily_loss_amount": self.get_max_daily_loss_amount(),
            "today_loss": self.get_today_loss(),
            "can_trade_today": self.can_trade_today(),
        }
