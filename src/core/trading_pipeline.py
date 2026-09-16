"""
TradingPipeline - AtriaTrade

Safe orchestration layer for:
- Paper Trading
- Backtesting
- Testnet

Important safety rule:
This module never submits real exchange orders.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


class TradingPipeline:
    """
    Coordinates market data, strategy signals, portfolio checks and recovery.

    The pipeline produces simulated decisions only. Any external execution
    layer must explicitly verify the environment before doing anything.
    """

    VALID_MODES = {"paper", "backtest", "testnet"}

    def __init__(
        self,
        portfolio_manager: Any,
        recovery_manager: Any,
        strategy: Optional[Callable[..., Any]] = None,
        mode: str = "paper",
        max_position_weight_pct: float = 100.0,
    ) -> None:
        normalized_mode = str(mode).strip().lower()

        if normalized_mode not in self.VALID_MODES:
            raise ValueError(
                f"mode must be one of: {sorted(self.VALID_MODES)}"
            )

        if portfolio_manager is None:
            raise ValueError("portfolio_manager is required.")

        if recovery_manager is None:
            raise ValueError("recovery_manager is required.")

        if max_position_weight_pct <= 0 or max_position_weight_pct > 100:
            raise ValueError(
                "max_position_weight_pct must be between 0 and 100."
            )

        self.portfolio_manager = portfolio_manager
        self.recovery_manager = recovery_manager
        self.strategy = strategy
        self.mode = normalized_mode
        self.max_position_weight_pct = float(max_position_weight_pct)

        self.cycle = 0
        self.running = False
        self.history: List[Dict[str, Any]] = []
        self.error_count = 0

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_signal(signal: Any) -> str:
        if signal is None:
            return "HOLD"

        if isinstance(signal, dict):
            signal = signal.get("signal", signal.get("action", "HOLD"))

        normalized = str(signal).strip().upper()

        aliases = {
            "BUY": "BUY",
            "LONG": "BUY",
            "SELL": "SELL",
            "SHORT": "SELL",
            "HOLD": "HOLD",
            "WAIT": "HOLD",
            "NONE": "HOLD",
        }

        return aliases.get(normalized, "HOLD")

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            result = float(value)
            if result != result:
                return default
            if result == float("inf") or result == float("-inf"):
                return default
            return result
        except (TypeError, ValueError):
            return default

    def _get_drawdown(self, market_data: Dict[str, Any]) -> float:
        if "drawdown_pct" in market_data:
            return max(0.0, self._safe_float(market_data["drawdown_pct"]))

        getter = getattr(self.portfolio_manager, "get_drawdown", None)
        if callable(getter):
            return max(0.0, self._safe_float(getter()))

        getter = getattr(self.portfolio_manager, "calculate_drawdown", None)
        if callable(getter):
            return max(0.0, self._safe_float(getter()))

        return 0.0

    def _generate_signal(self, market_data: Dict[str, Any]) -> str:
        if self.strategy is None:
            return self._normalize_signal(market_data.get("signal", "HOLD"))

        try:
            result = self.strategy(market_data)
        except TypeError:
            result = self.strategy()

        return self._normalize_signal(result)

    def _portfolio_allows(self, signal: str, market_data: Dict[str, Any]) -> bool:
        if signal == "HOLD":
            return True

        requested_weight = self._safe_float(
            market_data.get("position_weight_pct", 0.0)
        )

        if requested_weight > self.max_position_weight_pct:
            return False

        for method_name in (
            "can_trade",
            "can_open_position",
            "validate_trade",
        ):
            method = getattr(self.portfolio_manager, method_name, None)

            if callable(method):
                try:
                    result = method(
                        symbol=market_data.get("symbol"),
                        side=signal,
                        quantity=market_data.get("quantity", 0.0),
                    )
                except TypeError:
                    try:
                        result = method(signal)
                    except TypeError:
                        result = method()

                if result is False:
                    return False

        return True

    def process_cycle(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process one market-data cycle.

        Returns a decision record. No real order is submitted.
        """
        if not isinstance(market_data, dict):
            raise TypeError("market_data must be a dictionary.")

        self.cycle += 1

        try:
            drawdown = self._get_drawdown(market_data)
            recovery_result = self.recovery_manager.evaluate(drawdown)
            recovery_status = recovery_result.get("status", "normal")

            blocked_statuses = {
                "critical",
                "emergency_stop",
                "recovering",
                "cooldown",
            }

            signal = self._generate_signal(market_data)

            if recovery_status in blocked_statuses:
                decision = "BLOCKED_RECOVERY"

            elif signal == "HOLD":
                decision = "HOLD"

            elif not self._portfolio_allows(signal, market_data):
                decision = "BLOCKED_PORTFOLIO"

            else:
                decision = f"SIMULATED_{signal}"

            result = {
                "timestamp": self._timestamp(),
                "cycle": self.cycle,
                "mode": self.mode,
                "symbol": market_data.get("symbol"),
                "price": self._safe_float(market_data.get("price")),
                "signal": signal,
                "decision": decision,
                "drawdown_pct": drawdown,
                "recovery_status": recovery_status,
                "order_submitted": False,
                "real_trading_enabled": False,
                "error": None,
            }

            self.history.append(result)
            return result

        except Exception as exc:
            self.error_count += 1

            result = {
                "timestamp": self._timestamp(),
                "cycle": self.cycle,
                "mode": self.mode,
                "symbol": market_data.get("symbol"),
                "signal": "HOLD",
                "decision": "ERROR_SAFE_HOLD",
                "order_submitted": False,
                "real_trading_enabled": False,
                "error": str(exc),
            }

            self.history.append(result)
            return result

    def run(
        self,
        market_data_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Process multiple market-data records."""
        if not isinstance(market_data_list, list):
            raise TypeError("market_data_list must be a list.")

        self.running = True
        results: List[Dict[str, Any]] = []

        try:
            for market_data in market_data_list:
                results.append(self.process_cycle(market_data))
        finally:
            self.running = False

        return results

    def stop(self) -> None:
        """Stop the pipeline loop safely."""
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Return the current pipeline status."""
        return {
            "mode": self.mode,
            "cycle": self.cycle,
            "running": self.running,
            "history_count": len(self.history),
            "error_count": self.error_count,
            "order_submitted": False,
            "real_trading_enabled": False,
            "allowed_environments": sorted(self.VALID_MODES),
        }
