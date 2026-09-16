"""
Performance Analyzer for AtriaTrade.

Calculates key risk and return metrics: Sharpe, Sortino, Profit Factor,
Max Drawdown, Win Rate, and Average PnL.
Simulation and backtest analysis only.
"""

import math
from typing import Any, Dict, List, Optional


class PerformanceAnalyzer:
    """Calculates comprehensive trading performance and risk metrics."""

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        """
        Initialize analyzer.
        :param risk_free_rate: Annualized or per-period risk-free rate (default 0.0).
        """
        if risk_free_rate < 0:
            raise ValueError("risk_free_rate cannot be negative")
        self.risk_free_rate = float(risk_free_rate)

    @staticmethod
    def _validate_trades(trades: List[Dict[str, Any]]) -> None:
        if not isinstance(trades, list):
            raise TypeError("trades must be a list of dictionaries")
        for trade in trades:
            if not isinstance(trade, dict):
                raise TypeError("Each trade must be a dictionary")
            if "pnl" not in trade:
                raise ValueError("Each trade must contain a 'pnl' key")

    @staticmethod
    def _validate_equity_curve(equity_curve: List[float]) -> None:
        if not isinstance(equity_curve, list):
            raise TypeError("equity_curve must be a list of numbers")
        if len(equity_curve) < 1:
            raise ValueError("equity_curve cannot be empty")
        for value in equity_curve:
            try:
                val = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("equity_curve values must be numeric") from exc
            if val < 0:
                raise ValueError("equity values cannot be negative")

    def calculate_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """Calculate peak, trough, max drawdown percentage, and absolute drawdown."""
        self._validate_equity_curve(equity_curve)

        peak = float(equity_curve[0])
        max_dd_pct = 0.0
        max_dd_abs = 0.0

        for eq in equity_curve:
            eq_float = float(eq)
            if eq_float > peak:
                peak = eq_float

            if peak > 0:
                dd_abs = peak - eq_float
                dd_pct = (dd_abs / peak) * 100.0

                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                if dd_abs > max_dd_abs:
                    max_dd_abs = dd_abs

        return {
            "max_drawdown_percent": float(round(max_dd_pct, 4)),
            "max_drawdown_absolute": float(round(max_dd_abs, 4)),
            "peak_equity": float(round(peak, 4)),
        }

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        annualization_factor: float = 1.0,
    ) -> float:
        """
        Calculate Sharpe Ratio based on a sequence of percentage/decimal returns.
        Sharpe = (Mean Return - Rf) / StdDev(Return) * sqrt(factor)
        """
        if not returns or len(returns) < 2:
            return 0.0

        numeric_returns = [float(r) for r in returns]
        n = len(numeric_returns)
        mean_return = sum(numeric_returns) / n

        variance = sum((r - mean_return) ** 2 for r in numeric_returns) / (n - 1)
        if variance <= 0:
            return 0.0

        std_dev = math.sqrt(variance)
        if std_dev == 0:
            return 0.0

        excess_return = mean_return - self.risk_free_rate
        sharpe = (excess_return / std_dev) * math.sqrt(annualization_factor)
        return float(round(sharpe, 4))

    def calculate_sortino_ratio(
        self,
        returns: List[float],
        target_return: float = 0.0,
        annualization_factor: float = 1.0,
    ) -> float:
        """
        Calculate Sortino Ratio (penalizes only downside volatility).
        Sortino = (Mean Return - Target) / Downside_StdDev * sqrt(factor)
        """
        if not returns or len(returns) < 2:
            return 0.0

        numeric_returns = [float(r) for r in returns]
        n = len(numeric_returns)
        mean_return = sum(numeric_returns) / n

        downside_diffs = [min(0.0, r - target_return) ** 2 for r in numeric_returns]
        downside_variance = sum(downside_diffs) / (n - 1)

        if downside_variance <= 0:
            return 0.0

        downside_dev = math.sqrt(downside_variance)
        if downside_dev == 0:
            return 0.0

        excess_return = mean_return - target_return
        sortino = (excess_return / downside_dev) * math.sqrt(annualization_factor)
        return float(round(sortino, 4))

    def analyze(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[float],
        initial_capital: float = 1000.0,
    ) -> Dict[str, Any]:
        """Full performance summary from trade history and equity curve."""
        self._validate_trades(trades)
        self._validate_equity_curve(equity_curve)

        if initial_capital <= 0:
            raise ValueError("initial_capital must be greater than zero")

        total_trades = len(trades)
        wins = [t for t in trades if float(t["pnl"]) > 0]
        losses = [t for t in trades if float(t["pnl"]) < 0]
        breakevens = [t for t in trades if float(t["pnl"]) == 0]

        wins_count = len(wins)
        losses_count = len(losses)
        breakeven_count = len(breakevens)

        gross_profit = sum(float(t["pnl"]) for t in wins)
        gross_loss = abs(sum(float(t["pnl"]) for t in losses))
        net_profit = gross_profit - gross_loss

        win_rate = (wins_count / total_trades * 100.0) if total_trades > 0 else 0.0

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = 999.0  # Cap when zero loss but positive profit
        else:
            profit_factor = 0.0

        avg_win = (gross_profit / wins_count) if wins_count > 0 else 0.0
        avg_loss = (gross_loss / losses_count) if losses_count > 0 else 0.0
        payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else (999.0 if avg_win > 0 else 0.0)

        # Trade percentage returns
        trade_returns = [float(t.get("pnl_percent", 0.0)) / 100.0 for t in trades]

        # Equity periodic returns
        equity_returns = []
        for i in range(1, len(equity_curve)):
            prev = float(equity_curve[i - 1])
            curr = float(equity_curve[i])
            if prev > 0:
                equity_returns.append((curr - prev) / prev)

        dd_metrics = self.calculate_drawdown(equity_curve)
        sharpe = self.calculate_sharpe_ratio(equity_returns if equity_returns else trade_returns)
        sortino = self.calculate_sortino_ratio(equity_returns if equity_returns else trade_returns)

        final_capital = float(equity_curve[-1])
        net_profit_pct = ((final_capital - initial_capital) / initial_capital) * 100.0

        return {
            "initial_capital": float(initial_capital),
            "final_capital": round(final_capital, 4),
            "net_profit": round(net_profit, 4),
            "net_profit_percent": round(net_profit_pct, 4),
            "total_trades": total_trades,
            "wins": wins_count,
            "losses": losses_count,
            "breakevens": breakeven_count,
            "win_rate_percent": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4),
            "average_win": round(avg_win, 4),
            "average_loss": round(avg_loss, 4),
            "payoff_ratio": round(payoff_ratio, 4),
            "max_drawdown_percent": dd_metrics["max_drawdown_percent"],
            "max_drawdown_absolute": dd_metrics["max_drawdown_absolute"],
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
        }
