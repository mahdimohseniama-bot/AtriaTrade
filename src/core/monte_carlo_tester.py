import random
from typing import Dict, Any, List


class MonteCarloStressTester:
    """
    موتور شبیه‌سازی و تست تنش مونت‌کارلو برای ارزیابی ریسک دنباله سود/زیان.
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital

    def run_simulation(
        self,
        trade_returns_pct: List[float],
        num_simulations: int = 500,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """
        اجرای شبیه‌سازی مونت‌کارلو با جابه‌جایی تصادفی درصد سود/زیان معاملات (Bootstrap).
        """
        if not trade_returns_pct or len(trade_returns_pct) < 2:
            return {
                "success": False,
                "reason": "INSUFFICIENT_TRADE_HISTORY",
                "simulations_run": 0,
            }

        rng = random.Random(random_seed)
        n_trades = len(trade_returns_pct)

        max_drawdowns: List[float] = []
        final_balances: List[float] = []
        ruin_count = 0  # افت بیش از ۵۰٪ به عنوان ورشکستگی فرضی

        for _ in range(num_simulations):
            # بازنمونه‌گیری با جایگذاری (Resampling with replacement)
            sim_trades = [rng.choice(trade_returns_pct) for _ in range(n_trades)]
            
            equity = self.initial_capital
            peak = self.initial_capital
            max_dd = 0.0

            for ret in sim_trades:
                equity *= (1.0 + ret / 100.0)
                if equity > peak:
                    peak = equity
                dd = ((peak - equity) / peak) * 100.0 if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

            max_drawdowns.append(max_dd)
            final_balances.append(equity)
            if max_dd >= 50.0:
                ruin_count += 1

        max_drawdowns.sort()
        final_balances.sort()

        # محاسبه صدک ۹۵ام Max Drawdown (بدترین سناریو با ضریب اطمینان ۹۵٪)
        p95_idx = int(0.95 * num_simulations)
        p50_idx = int(0.50 * num_simulations)

        p95_max_dd = max_drawdowns[min(p95_idx, num_simulations - 1)]
        median_final_equity = final_balances[min(p50_idx, num_simulations - 1)]
        ruin_probability = (ruin_count / num_simulations) * 100.0

        return {
            "success": True,
            "simulations_run": num_simulations,
            "p95_max_drawdown_pct": round(p95_max_dd, 2),
            "median_final_equity": round(median_final_equity, 2),
            "ruin_probability_pct": round(ruin_probability, 2),
            "is_robust": p95_max_dd < 30.0 and ruin_probability < 5.0,
        }
