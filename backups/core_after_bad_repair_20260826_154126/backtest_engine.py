"""
Backtest Engine for AtriaTrade.

This module runs a trading strategy against historical OHLCV data.
It is simulation-only and does not connect to any exchange.
"""

from typing import Any, Dict, List, Optional


class BacktestEngine:
    """Simulation-only engine for testing trading strategies."""

    def __init__(
        self,
        strategy: Any,
        initial_capital: float = 1000.0,
        fee_rate: float = 0.001,
    ) -> None:
        if strategy is None:
            raise ValueError("strategy is required")

        if initial_capital <= 0:
            raise ValueError("initial_capital must be greater than zero")

        if fee_rate < 0:
            raise ValueError("fee_rate cannot be negative")

        self.strategy = strategy
        self.initial_capital = float(initial_capital)
        self.fee_rate = float(fee_rate)

        self.capital: float = self.initial_capital
        self.position: Optional[Dict[str, Any]] = None
        self.trades_history: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = [self.initial_capital]

    def reset(self) -> None:
        """Reset all simulation state."""
        self.capital = self.initial_capital
        self.position = None
        self.trades_history = []
        self.equity_curve = [self.initial_capital]

    @staticmethod
    def _validate_candle(candle: Dict[str, Any]) -> None:
        """Validate one historical OHLCV candle."""
        if not isinstance(candle, dict):
            raise TypeError("Each historical candle must be a dictionary")

        if "close" not in candle:
            raise ValueError("Each candle must contain a close value")

        try:
            close_price = float(candle["close"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Candle close must be numeric") from exc

        if close_price <= 0:
            raise ValueError("Candle close must be greater than zero")

    @staticmethod
    def _normalize_signal(signal: Any) -> str:
        """Normalize strategy output to BUY, SELL, or HOLD."""
        if hasattr(signal, "value"):
            signal = signal.value

        if signal is None:
            return "HOLD"

        normalized = str(signal).strip().upper()

        if normalized not in {"BUY", "SELL", "HOLD"}:
            return "HOLD"

        return normalized

    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current account equity."""
        if self.position is None:
            return float(self.capital)

        position_value = self.position["quantity"] * current_price
        return float(position_value)

    def _open_position(
        self,
        symbol: str,
        price: float,
        timestamp: Any,
    ) -> None:
        """Open a long position using all available capital."""
        if self.position is not None:
            return

        if self.capital <= 0:
            return

        gross_capital = float(self.capital)
        entry_fee = gross_capital * self.fee_rate
        investable_capital = gross_capital - entry_fee

        if investable_capital <= 0:
            return

        quantity = investable_capital / price

        self.position = {
            "symbol": symbol,
            "entry_price": float(price),
            "quantity": float(quantity),
            "entry_time": timestamp,
            "invested": gross_capital,
            "entry_fee": entry_fee,
        }

        self.capital = 0.0

    def _close_position(
        self,
        symbol: str,
        price: float,
        timestamp: Any,
        closed_at_end: bool = False,
    ) -> None:
        """Close the current long position and save trade information."""
        if self.position is None:
            return

        gross_return = self.position["quantity"] * price
        exit_fee = gross_return * self.fee_rate
        net_return = gross_return - exit_fee

        invested = self.position["invested"]
        pnl = net_return - invested

        if invested > 0:
            pnl_percent = (pnl / invested) * 100.0
        else:
            pnl_percent = 0.0

        trade = {
            "symbol": symbol,
            "entry_price": round(self.position["entry_price"], 8),
            "exit_price": round(price, 8),
            "quantity": round(self.position["quantity"], 8),
            "entry_time": self.position["entry_time"],
            "exit_time": timestamp,
            "invested": round(invested, 8),
            "entry_fee": round(self.position["entry_fee"], 8),
            "exit_fee": round(exit_fee, 8),
            "gross_return": round(gross_return, 8),
            "net_return": round(net_return, 8),
            "pnl": round(pnl, 8),
            "pnl_percent": round(pnl_percent, 8),
        }

        if closed_at_end:
            trade["closed_at_end"] = True

        self.trades_history.append(trade)
        self.capital = float(net_return)
        self.position = None

    def run(
        self,
        historical_data: List[Dict[str, Any]],
        symbol: str = "BTCUSDT",
    ) -> Dict[str, Any]:
        """
        Run the strategy over historical OHLCV candles.

        The strategy receives only close prices.
        This is compatible with SMACrossStrategy.
        """
        if not isinstance(historical_data, list):
            raise TypeError("historical_data must be a list")

        if len(historical_data) < 5:
            raise ValueError(
                "At least 5 historical candles are required"
            )

        self.reset()

        for index, candle in enumerate(historical_data):
            self._validate_candle(candle)

            current_price = float(candle["close"])
            timestamp = candle.get("timestamp", index)

            window = historical_data[: index + 1]

            close_prices = [
                float(window_candle["close"])
                for window_candle in window
            ]

            strategy_signal = self.strategy.generate_signal(close_prices)
            signal = self._normalize_signal(strategy_signal)

            if signal == "BUY" and self.position is None:
                self._open_position(
                    symbol=symbol,
                    price=current_price,
                    timestamp=timestamp,
                )

            elif signal == "SELL" and self.position is not None:
                self._close_position(
                    symbol=symbol,
                    price=current_price,
                    timestamp=timestamp,
                )

            current_equity = self._calculate_equity(current_price)
            self.equity_curve.append(round(current_equity, 8))

        if self.position is not None:
            last_candle = historical_data[-1]
            last_price = float(last_candle["close"])
            last_timestamp = last_candle.get(
                "timestamp",
                len(historical_data) - 1,
            )

            self._close_position(
                symbol=symbol,
                price=last_price,
                timestamp=last_timestamp,
                closed_at_end=True,
            )

            self.equity_curve[-1] = round(self.capital, 8)

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Return performance metrics."""
        total_trades = len(self.trades_history)

        wins = [
            trade
            for trade in self.trades_history
            if trade["pnl"] > 0
        ]

        losses = [
            trade
            for trade in self.trades_history
            if trade["pnl"] <= 0
        ]

        wins_count = len(wins)
        losses_count = len(losses)

        if total_trades > 0:
            win_rate_percent = (
                wins_count / total_trades
            ) * 100.0
        else:
            win_rate_percent = 0.0

        net_profit = self.capital - self.initial_capital

        net_profit_percent = (
            net_profit / self.initial_capital
        ) * 100.0

        peak_equity = self.initial_capital
        max_drawdown_percent = 0.0

        for equity in self.equity_curve:
            if equity > peak_equity:
                peak_equity = equity

            if peak_equity > 0:
                drawdown_percent = (
                    (peak_equity - equity) / peak_equity
                ) * 100.0

                if drawdown_percent > max_drawdown_percent:
                    max_drawdown_percent = drawdown_percent

        return {
            "initial_capital": float(self.initial_capital),
            "final_capital": float(round(self.capital, 8)),
            "net_profit": float(round(net_profit, 8)),
            "net_profit_percent": float(
                round(net_profit_percent, 8)
            ),
            "total_trades": int(total_trades),
            "wins": int(wins_count),
            "losses": int(losses_count),
            "win_rate_percent": float(
                round(win_rate_percent, 8)
            ),
            "max_drawdown_percent": float(
                round(max_drawdown_percent, 8)
            ),
            "closed_trades": list(self.trades_history),
            "equity_curve": list(self.equity_curve),
        }
