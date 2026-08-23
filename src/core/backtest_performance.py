"""
Backtest Performance Integration for AtriaTrade.

Connects BacktestEngine results to PerformanceAnalyzer.

Simulation-only module.
No exchange connection.
No real trading.
"""

from typing import Any, Dict

from src.core.performance_analyzer import PerformanceAnalyzer


class BacktestPerformance:
    """
    Connects BacktestEngine output to PerformanceAnalyzer.

    Expected result structure:

    {
        "initial_capital": float,
        "final_capital": float,
        "closed_trades": list,
        "equity_curve": list
    }
    """

    REQUIRED_KEYS = (
        "initial_capital",
        "final_capital",
        "closed_trades",
        "equity_curve",
    )

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        self.analyzer = PerformanceAnalyzer(
            risk_free_rate=risk_free_rate
        )

    @classmethod
    def _validate_backtest_result(
        cls,
        backtest_result: Dict[str, Any],
    ) -> None:
        """Validate the minimum required backtest result structure."""
        if not isinstance(backtest_result, dict):
            raise TypeError(
                "backtest_result must be a dictionary"
            )

        for key in cls.REQUIRED_KEYS:
            if key not in backtest_result:
                raise ValueError(
                    f"backtest_result is missing required key: {key}"
                )

        try:
            initial_capital = float(
                backtest_result["initial_capital"]
            )
            float(backtest_result["final_capital"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "initial_capital and final_capital must be numeric"
            ) from exc

        if initial_capital <= 0:
            raise ValueError(
                "initial_capital must be greater than zero"
            )

        if not isinstance(
            backtest_result["closed_trades"],
            list,
        ):
            raise TypeError(
                "closed_trades must be a list"
            )

        if not isinstance(
            backtest_result["equity_curve"],
            list,
        ):
            raise TypeError(
                "equity_curve must be a list"
            )

        if len(backtest_result["equity_curve"]) == 0:
            raise ValueError(
                "equity_curve cannot be empty"
            )

    def analyze(
        self,
        backtest_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze one completed backtest result.

        Returns a combined report containing:
        - backtest summary
        - performance metrics
        """
        self._validate_backtest_result(backtest_result)

        initial_capital = float(
            backtest_result["initial_capital"]
        )

        final_capital = float(
            backtest_result["final_capital"]
        )

        closed_trades = list(
            backtest_result["closed_trades"]
        )

        equity_curve = list(
            backtest_result["equity_curve"]
        )

        performance = self.analyzer.analyze(
            trades=closed_trades,
            equity_curve=equity_curve,
            initial_capital=initial_capital,
        )

        return {
            "backtest": {
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "total_trades": len(closed_trades),
                "equity_curve": equity_curve,
                "closed_trades": closed_trades,
            },
            "performance": performance,
        }

    def analyze_engine(
        self,
        engine: Any,
        historical_data: list,
        symbol: str = "BTCUSDT",
    ) -> Dict[str, Any]:
        """
        Run a backtest engine and analyze its result.

        The engine must provide:
            run(historical_data=..., symbol=...)
        """
        if engine is None:
            raise ValueError("engine is required")

        if not hasattr(engine, "run"):
            raise TypeError(
                "engine must provide a run() method"
            )

        backtest_result = engine.run(
            historical_data=historical_data,
            symbol=symbol,
        )

        return self.analyze(backtest_result)
