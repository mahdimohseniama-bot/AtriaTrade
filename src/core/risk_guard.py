# -*- coding: utf-8 -*-
"""
AtriaTrade Risk & Profit Guard Engine
Designed for conservative, capital-preserving paper trading & live readiness.
"""

from decimal import Decimal
from typing import Dict, Any

class RiskProfitGuard:
    def __init__(self, initial_capital: float = 10000.0, max_daily_loss_pct: float = 2.0):
        self.initial_capital = Decimal(str(initial_capital))
        self.current_balance = Decimal(str(initial_capital))
        self.profit_reserve = Decimal("0.0")
        self.max_daily_loss_pct = Decimal(str(max_daily_loss_pct))
        self.daily_pnl = Decimal("0.0")
        self.is_locked = False

    def can_open_position(self, proposed_risk_amount: float) -> Dict[str, Any]:
        risk = Decimal(str(proposed_risk_amount))
        if self.is_locked:
            return {"allowed": False, "reason": "گارد ریسک قفل است (سقف ضرر روزانه فعال شده)"}
        
        # محاسبه حداکثر افت مجاز روزانه
        max_allowed_loss = self.initial_capital * (self.max_daily_loss_pct / Decimal("100"))
        if (self.daily_pnl - risk).copy_abs() > max_allowed_loss and (self.daily_pnl - risk) < 0:
            return {"allowed": False, "reason": "این معامله از سقف ریسک مجاز ۲٪ روزانه فراتر می‌رود"}
            
        return {"allowed": True, "reason": "معامله در محدوده امن و مجاز است"}

    def on_trade_closed(self, pnl: float) -> Dict[str, Any]:
        trade_pnl = Decimal(str(pnl))
        self.daily_pnl += trade_pnl
        
        if trade_pnl > 0:
            # جداسازی سود و انتقال مستقیم به صندوق رزرو
            self.profit_reserve += trade_pnl
            msg = f"سود {trade_pnl} دلاری به صندوق رزرو منتقل شد و از اصل سرمایه جدا گردید."
        else:
            self.current_balance += trade_pnl
            msg = f"ضرر {trade_pnl.copy_abs()} دلاری ثبت شد."
            
        # بررسی سقف ضرر روزانه
        max_allowed_loss = self.initial_capital * (self.max_daily_loss_pct / Decimal("100"))
        if self.daily_pnl < 0 and self.daily_pnl.copy_abs() >= max_allowed_loss:
            self.is_locked = True
            msg += " [هشدار: سقف ضرر روزانه فعال شد، بات برای امروز قفل گردید]"

        return {
            "current_balance": float(self.current_balance),
            "profit_reserve": float(self.profit_reserve),
            "daily_pnl": float(self.daily_pnl),
            "is_locked": self.is_locked,
            "message": msg
        }

    def get_guard_status(self) -> Dict[str, Any]:
        return {
            "initial_capital": float(self.initial_capital),
            "current_balance": float(self.current_balance),
            "profit_reserve": float(self.profit_reserve),
            "daily_pnl": float(self.daily_pnl),
            "is_locked": self.is_locked
        }

if __name__ == "__main__":
    guard = RiskProfitGuard(10000.0, 2.0)
    assert guard.can_open_position(100.0)["allowed"] == True
    # شبیه‌سازی معامله سودده
    res = guard.on_trade_closed(150.0)
    assert res["profit_reserve"] == 150.0
    print("SUCCESS: RiskProfitGuard Engine Tested & Passed!")
