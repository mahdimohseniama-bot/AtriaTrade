"""Portfolio Risk Manager module for AtriaTrade (Pure Python).

Provides aggregate portfolio-level risk limits, exposure checks,
and correlated asset protection.
"""

from typing import Dict, List, Any, Optional


class PortfolioRiskManager:
    def __init__(
        self,
        max_total_exposure_pct: float = 0.80,      # حداکثر ۸۰ درصد کل پورتفوی در معامله درگیر باشد
        max_single_asset_exposure_pct: float = 0.30,# حداکثر ۳۰ درصد برای یک دارایی واحد
        max_open_positions: int = 5,               # حداکثر ۵ پوزیشن باز همزمان
        max_correlated_exposure_pct: float = 0.50, # حداکثر ۵۰ درصد در دارایی‌های همبسته
        max_portfolio_daily_loss_pct: float = 0.05 # حداکثر ۵ درصد حد ضرر روزانه کل سبد
    ):
        self.max_total_exposure_pct = float(max_total_exposure_pct)
        self.max_single_asset_exposure_pct = float(max_single_asset_exposure_pct)
        self.max_open_positions = int(max_open_positions)
        self.max_correlated_exposure_pct = float(max_correlated_exposure_pct)
        self.max_portfolio_daily_loss_pct = float(max_portfolio_daily_loss_pct)

    def validate_new_position(
        self,
        portfolio_balance: float,
        current_positions: List[Dict[str, Any]],
        new_symbol: str,
        new_position_value: float,
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None,
        daily_pnl_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Validates if a new trade can be opened without violating portfolio limits."""
        if portfolio_balance <= 0:
            return {"allowed": False, "reason": "Portfolio balance must be positive"}

        if new_position_value <= 0:
            return {"allowed": False, "reason": "New position value must be positive"}

        # ۱. بررسی سقف افت روزانه پورتفوی
        if daily_pnl_pct <= -self.max_portfolio_daily_loss_pct:
            return {
                "allowed": False,
                "reason": f"Daily portfolio loss limit reached ({daily_pnl_pct * 100:.2f}%)"
            }

        # ۲. بررسی حداکثر تعداد پوزیشن‌های باز
        if len(current_positions) >= self.max_open_positions:
            return {
                "allowed": False,
                "reason": f"Maximum open positions ({self.max_open_positions}) reached"
            }

        # محاسبه ارزش‌های موجود
        current_total_exposure = sum(float(p.get("value", 0.0)) for p in current_positions)
        new_total_exposure = current_total_exposure + new_position_value
        total_exposure_pct = new_total_exposure / portfolio_balance

        # ۳. بررسی کل اکسپوژر پورتفوی
        if total_exposure_pct > self.max_total_exposure_pct:
            return {
                "allowed": False,
                "reason": f"Total exposure ({total_exposure_pct * 100:.1f}%) exceeds limit ({self.max_total_exposure_pct * 100:.1f}%)"
            }

        # ۴. بررسی سقف تخصیص به یک دارایی واحد
        existing_symbol_value = sum(
            float(p.get("value", 0.0))
            for p in current_positions
            if p.get("symbol") == new_symbol
        )
        new_symbol_exposure = existing_symbol_value + new_position_value
        symbol_exposure_pct = new_symbol_exposure / portfolio_balance

        if symbol_exposure_pct > self.max_single_asset_exposure_pct:
            return {
                "allowed": False,
                "reason": f"Single asset exposure for {new_symbol} ({symbol_exposure_pct * 100:.1f}%) exceeds limit ({self.max_single_asset_exposure_pct * 100:.1f}%)"
            }

        # ۵. بررسی همبستگی با پوزیشن‌های فعلی
        if correlation_matrix and new_symbol in correlation_matrix:
            correlated_value = new_position_value
            for pos in current_positions:
                sym = pos.get("symbol")
                val = float(pos.get("value", 0.0))
                corr = correlation_matrix[new_symbol].get(sym, 0.0)
                # اگر همبستگی بالای ۰.۷ باشد، در گروه ریسک متمرکز قرار می‌گیرد
                if corr >= 0.70:
                    correlated_value += val

            correlated_exposure_pct = correlated_value / portfolio_balance
            if correlated_exposure_pct > self.max_correlated_exposure_pct:
                return {
                    "allowed": False,
                    "reason": f"Correlated exposure for {new_symbol} ({correlated_exposure_pct * 100:.1f}%) exceeds limit ({self.max_correlated_exposure_pct * 100:.1f}%)"
                }

        return {
            "allowed": True,
            "projected_total_exposure_pct": round(total_exposure_pct, 4),
            "projected_symbol_exposure_pct": round(symbol_exposure_pct, 4)
        }
