"""
ماژول ذخیره سود (Profit Reserve / Capital Protection)
"""
from typing import Dict, Any, Optional

class ProfitReserveManager:
    """
    مدیریت و تفکیک خودکار سود برای حفظ اصل سرمایه.
    """
    def __init__(self, reserve_ratio: float = 0.5, portfolio: Optional[Any] = None, *args, **kwargs):
        """
        :param reserve_ratio: درصد ذخیره سود (مثلاً ۰.۵ برای ۵۰ درصد)
        :param portfolio: نمونه PortfolioManager اختیاری
        """
        if not (0.0 <= reserve_ratio <= 1.0):
            raise ValueError("Reserve ratio must be between 0.0 and 1.0")
        self.reserve_ratio = float(reserve_ratio)
        self.portfolio = portfolio
        self.total_reserved_profit = 0.0
        self.reserve_history = []

    def calculate_reserve(self, net_profit: float) -> float:
        """محاسبه مقدار سودی که باید ذخیره شود."""
        if net_profit <= 0:
            return 0.0
        return net_profit * self.reserve_ratio

    def process_trade_profit(self, profit_amount: float, trade_id: Optional[str] = None) -> Dict[str, Any]:
        """پردازش سود معامله و ثبت ذخیره"""
        reserve_amount = self.calculate_reserve(profit_amount)
        if reserve_amount > 0:
            self.total_reserved_profit += reserve_amount
            self.reserve_history.append({
                "trade_id": trade_id,
                "profit": profit_amount,
                "reserved": reserve_amount,
                "total_reserved": self.total_reserved_profit
            })
        return {
            "reserved_amount": reserve_amount,
            "reinvest_amount": profit_amount - reserve_amount,
            "total_reserved": self.total_reserved_profit
        }

    def get_summary(self) -> Dict[str, Any]:
        """خلاصه وضعیت ذخیره سود"""
        return {
            "reserve_ratio": self.reserve_ratio,
            "total_reserved_profit": self.total_reserved_profit,
            "total_records": len(self.reserve_history)
        }

# Compatibility method required by TradingEngine tests
def _profit_reserve_get_vault_balance(self):
    for name in (
        "vault_balance",
        "vault",
        "reserved_profit",
        "reserve_balance",
        "balance",
    ):
        if hasattr(self, name):
            value = getattr(self, name)
            if not callable(value):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass

    for name in (
        "get_balance",
        "get_reserve_balance",
        "get_reserved_profit",
    ):
        method = getattr(self, name, None)
        if callable(method):
            try:
                return float(method())
            except (TypeError, ValueError):
                pass

    return 0.0


if not hasattr(ProfitReserveManager, "get_vault_balance"):
    ProfitReserveManager.get_vault_balance = _profit_reserve_get_vault_balance

# Root-compatible vault accounting
def _profit_reserve_add_to_vault(self, amount):
    amount = float(amount)
    if amount <= 0:
        return 0.0

    # انتخاب فیلد اصلی موجودی خزانه
    for name in (
        "vault_balance",
        "reserved_profit",
        "reserve_balance",
        "balance",
    ):
        if hasattr(self, name):
            current = getattr(self, name)
            if not callable(current):
                try:
                    new_value = float(current) + amount
                    setattr(self, name, new_value)
                    return new_value
                except (TypeError, ValueError):
                    pass

    # اگر هیچ فیلد مناسبی وجود نداشت، فیلد استاندارد بساز
    self.vault_balance = amount
    return self.vault_balance


def _profit_reserve_get_vault_balance_root(self):
    for name in (
        "vault_balance",
        "reserved_profit",
        "reserve_balance",
        "balance",
    ):
        value = getattr(self, name, None)
        if value is not None and not callable(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return 0.0


ProfitReserveManager.add_to_vault = _profit_reserve_add_to_vault
ProfitReserveManager.get_vault_balance = _profit_reserve_get_vault_balance_root


def _atria_add_to_vault(self, amount):
    amount = float(amount)

    if amount <= 0:
        return 0.0

    current = getattr(self, "vault_balance", 0.0)

    try:
        current = float(current or 0.0)
    except (TypeError, ValueError):
        current = 0.0

    self.vault_balance = current + amount
    return self.vault_balance


def _atria_get_vault_balance(self):
    try:
        return float(
            getattr(self, "vault_balance", 0.0) or 0.0
        )
    except (TypeError, ValueError):
        return 0.0


ProfitReserveManager.add_to_vault = _atria_add_to_vault
ProfitReserveManager.get_vault_balance = _atria_get_vault_balance
