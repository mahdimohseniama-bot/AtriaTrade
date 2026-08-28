from typing import Dict, Any
from datetime import datetime, timezone


class PortfolioDrawdownCircuitBreaker:
    """
    مدار شکن خودکار پایش افت سرمایه پورتفولیو جهت حفاظت از سرمایه در شرایط بحرانی بازار.
    """

    def __init__(
        self,
        max_total_drawdown_pct: float = 10.0,
        max_daily_drawdown_pct: float = 4.0,
        warning_drawdown_pct: float = 5.0,
    ):
        self.max_total_drawdown_pct = max_total_drawdown_pct
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.warning_drawdown_pct = warning_drawdown_pct

        self.peak_equity: float = 0.0
        self.day_start_equity: float = 0.0
        self.is_tripped: bool = False
        self.trip_reason: str = ""
        self.tripped_at: str = ""

    def update_equity(self, current_equity: float, is_new_day: bool = False) -> Dict[str, Any]:
        """
        به‌روزرسانی ارزش پورتفولیو و بررسی فعال شدن مدار شکن.
        """
        if current_equity <= 0:
            return {"status": "INVALID_EQUITY", "is_tripped": self.is_tripped}

        if self.peak_equity == 0.0 or current_equity > self.peak_equity:
            self.peak_equity = current_equity

        if self.day_start_equity == 0.0 or is_new_day:
            self.day_start_equity = current_equity

        # محاسبه افت کل و افت روزانه
        total_dd_pct = ((self.peak_equity - current_equity) / self.peak_equity) * 100.0
        daily_dd_pct = ((self.day_start_equity - current_equity) / self.day_start_equity) * 100.0 if self.day_start_equity > 0 else 0.0

        risk_scale = 1.0

        if total_dd_pct >= self.max_total_drawdown_pct:
            self.is_tripped = True
            self.trip_reason = f"MAX_TOTAL_DRAWDOWN_EXCEEDED: {total_dd_pct:.2f}%"
            self.tripped_at = datetime.now(timezone.utc).isoformat()
            risk_scale = 0.0
        elif daily_dd_pct >= self.max_daily_drawdown_pct:
            self.is_tripped = True
            self.trip_reason = f"MAX_DAILY_DRAWDOWN_EXCEEDED: {daily_dd_pct:.2f}%"
            self.tripped_at = datetime.now(timezone.utc).isoformat()
            risk_scale = 0.0
        elif total_dd_pct >= self.warning_drawdown_pct:
            # افت هشدار -> کاهش ریسک به ۵۰٪
            risk_scale = 0.5

        return {
            "is_tripped": self.is_tripped,
            "total_drawdown_pct": round(total_dd_pct, 2),
            "daily_drawdown_pct": round(daily_dd_pct, 2),
            "risk_multiplier": risk_scale,
            "trip_reason": self.trip_reason,
            "peak_equity": self.peak_equity,
        }

    def can_open_new_trade() -> bool:
        """بررسی مجاز بودن باز کردن معامله جدید"""
        pass

    def can_open_new_trade(self) -> bool:
        return not self.is_tripped

    def reset_circuit_breaker(self, reset_peak: bool = False, current_equity: float = 0.0):
        """ریست دستی یا پس از پایان بحران"""
        self.is_tripped = False
        self.trip_reason = ""
        self.tripped_at = ""
        if reset_peak and current_equity > 0:
            self.peak_equity = current_equity
            self.day_start_equity = current_equity
