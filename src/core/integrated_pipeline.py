"""
IntegratedTradingPipeline - AtriaTrade

Integrates:
- PortfolioManager (asset allocations & holdings)
- RecoveryManager (drawdown protection & emergency controls)
- TradingPipeline (signal evaluation & safe routing)
- ExecutionSimulator (virtual execution & trade fees)

Strictly Paper Trading / Backtest / Testnet.
Real trading is completely disabled.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.core.execution_simulator import ExecutionSimulator
from src.core.portfolio_manager import PortfolioManager
from src.core.recovery_manager import RecoveryManager
from src.core.trading_pipeline import TradingPipeline


class IntegratedTradingPipeline:
    """End-to-end simulated trading workflow pipeline."""

    VALID_MODES = {"paper", "backtest", "testnet"}

    def __init__(
        self,
        initial_cash: float = 10000.0,
        fee_pct: float = 0.1,
        mode: str = "paper",
        strategy_callback: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        max_drawdown_pct: float = 20.0,
    ) -> None:
        norm_mode = str(mode).strip().lower()
        if norm_mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of: {sorted(self.VALID_MODES)}")

        self.mode = norm_mode
        self.initial_cash = float(initial_cash)
        self.fee_pct = float(fee_pct)

        self.portfolio_manager = PortfolioManager(
            initial_cash=self.initial_cash,
        )
        self.recovery_manager = RecoveryManager(
            max_drawdown_pct=float(max_drawdown_pct),
            mode=self.mode,
        )
        self.simulator = ExecutionSimulator(
            initial_cash=self.initial_cash,
            fee_pct=self.fee_pct,
            mode=self.mode,
        )
        self.pipeline = TradingPipeline(
            portfolio_manager=self.portfolio_manager,
            recovery_manager=self.recovery_manager,
            strategy=strategy_callback,
            mode=self.mode,
        )

        self.execution_log: List[Dict[str, Any]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def process_tick(
        self,
        symbol: str,
        price: float,
        quantity: float,
        strategy_signal: Optional[str] = None,
        extra_market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process incoming tick data safely through the entire simulation stack.
        """
        sym = str(symbol).strip().upper()
        px = float(price)
        qty = float(quantity)

        # 1. Update mark-to-market equity and calculate drawdown
        current_equity = self.simulator.mark_to_market({sym: px})
        current_dd = self.portfolio_manager.calculate_drawdown(current_equity)
        rec_status = self.recovery_manager.evaluate(current_dd)

        # 2. Check if recovery manager or emergency breaker blocks trades
        recovery_locked = self.recovery_manager.get_status().get("is_active", False)

        # 3. Prepare pipeline input
        payload: Dict[str, Any] = {
            "symbol": sym,
            "price": px,
            "quantity": qty,
            "action": strategy_signal or "HOLD",
        }
        if extra_market_data:
            payload.update(extra_market_data)

        # 4. Process cycle in TradingPipeline
        pipe_res = self.pipeline.process_cycle(payload)

        # Resolve pipeline decision
        pipe_decision = str(pipe_res.get("decision", "HOLD")).upper()
        pipe_signal = str(pipe_res.get("signal") or pipe_res.get("action") or "HOLD").upper()

        is_blocked = (
            recovery_locked
            or "SAFE_HOLD" in pipe_decision
            or "RECOVERY" in pipe_decision
            or "EMERGENCY" in pipe_decision
            or pipe_signal == "HOLD"
        )

        if is_blocked:
            record = {
                "timestamp": self._timestamp(),
                "symbol": sym,
                "action": "HOLD",
                "pipeline_decision": pipe_res,
                "recovery_status": rec_status,
                "order_submitted": False,
                "real_trading_enabled": False,
                "simulated": True,
            }
            self.execution_log.append(record)
            return record

        action = pipe_signal if pipe_signal in {"BUY", "SELL"} else "HOLD"
        if action == "HOLD":
            record = {
                "timestamp": self._timestamp(),
                "symbol": sym,
                "action": "HOLD",
                "pipeline_decision": pipe_res,
                "recovery_status": rec_status,
                "order_submitted": False,
                "real_trading_enabled": False,
                "simulated": True,
            }
            self.execution_log.append(record)
            return record

        # 5. Virtual order execution via simulator
        sim_res = self.simulator.execute(
            symbol=sym,
            side=action,
            quantity=qty,
            price=px,
        )

        # 6. Mirror executed trade in PortfolioManager
        if sim_res.get("status") == "filled":
            fee = sim_res.get("fee", 0.0)
            if action == "BUY":
                self.portfolio_manager.record_buy(sym, qty, px, fee)
            elif action == "SELL":
                self.portfolio_manager.record_sell(sym, qty, px, fee)

        updated_equity = self.simulator.mark_to_market({sym: px})

        result = {
            "timestamp": self._timestamp(),
            "symbol": sym,
            "action": action,
            "pipeline_decision": pipe_res,
            "execution": sim_res,
            "equity": updated_equity,
            "order_submitted": False,
            "real_trading_enabled": False,
            "simulated": True,
        }
        self.execution_log.append(result)
        return result

    def get_full_status(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Aggregate complete system status."""
        prices = current_prices or {}
        eq = self.simulator.mark_to_market(prices)

        return {
            "mode": self.mode,
            "equity": eq,
            "cash": self.simulator.cash,
            "positions": dict(self.simulator.positions),
            "realized_pnl": self.simulator.realized_pnl,
            "trade_count": self.simulator.trade_count,
            "drawdown_status": self.recovery_manager.get_status(),
            "portfolio_summary": self.portfolio_manager.get_summary(prices),
            "order_submitted": False,
            "real_trading_enabled": False,
            "simulated_only": True,
        }
