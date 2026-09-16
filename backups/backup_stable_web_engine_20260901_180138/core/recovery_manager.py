"""
RecoveryManager - AtriaTrade

Safe recovery controller for Paper Trading, Backtesting and Testnet.
This module does not place real orders and does not perform deposits,
withdrawals or transfers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class RecoveryManager:
    """
    Monitors drawdown and defines safe recovery actions.

    Recovery actions are recommendations only. They must be executed by
    another explicitly approved simulation/testnet layer.
    """

    VALID_MODES = {"paper", "backtest", "testnet"}

    def __init__(
        self,
        max_drawdown_pct: float = 20.0,
        recovery_target_pct: float = 5.0,
        cooldown_cycles: int = 3,
        mode: str = "paper",
    ) -> None:
        if max_drawdown_pct <= 0 or max_drawdown_pct > 100:
            raise ValueError("max_drawdown_pct must be between 0 and 100.")

        if recovery_target_pct < 0 or recovery_target_pct >= max_drawdown_pct:
            raise ValueError(
                "recovery_target_pct must be >= 0 and lower than max_drawdown_pct."
            )

        if cooldown_cycles < 0:
            raise ValueError("cooldown_cycles cannot be negative.")

        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in self.VALID_MODES:
            raise ValueError(
                f"mode must be one of: {sorted(self.VALID_MODES)}"
            )

        self.max_drawdown_pct = float(max_drawdown_pct)
        self.recovery_target_pct = float(recovery_target_pct)
        self.cooldown_cycles = int(cooldown_cycles)
        self.mode = normalized_mode

        self.current_cycle = 0
        self.last_recovery_cycle: Optional[int] = None
        self.recovery_active = False
        self.emergency_stop = False
        self.history: List[Dict[str, Any]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_drawdown(drawdown_pct: float) -> float:
        value = float(drawdown_pct)

        if value < 0:
            raise ValueError("drawdown_pct cannot be negative.")

        if value != value or value == float("inf"):
            raise ValueError("drawdown_pct must be a finite number.")

        return value

    def advance_cycle(self, cycles: int = 1) -> int:
        """Advance the internal simulation/backtest cycle counter."""
        if cycles < 0:
            raise ValueError("cycles cannot be negative.")

        self.current_cycle += int(cycles)
        return self.current_cycle

    def is_in_cooldown(self) -> bool:
        """Return whether recovery is temporarily blocked by cooldown."""
        if self.last_recovery_cycle is None:
            return False

        return (
            self.current_cycle - self.last_recovery_cycle
            < self.cooldown_cycles
        )

    def evaluate(self, drawdown_pct: float) -> Dict[str, Any]:
        """
        Evaluate current drawdown and return a safe recovery decision.

        No order is submitted by this method.
        """
        drawdown = self._validate_drawdown(drawdown_pct)

        if self.emergency_stop:
            status = "emergency_stop"
            action = "halt_simulation"
            reason = "Emergency stop is active."

        elif drawdown >= self.max_drawdown_pct:
            self.recovery_active = True
            self.last_recovery_cycle = self.current_cycle
            status = "critical"
            action = "reduce_risk_and_pause_entries"
            reason = "Maximum permitted drawdown has been reached."

        elif self.recovery_active and drawdown <= self.recovery_target_pct:
            self.recovery_active = False
            status = "recovered"
            action = "resume_with_normal_risk"
            reason = "Drawdown returned to the recovery target."

        elif self.recovery_active:
            status = "recovering"
            action = "maintain_reduced_risk"
            reason = "Recovery mode remains active."

        elif self.is_in_cooldown():
            status = "cooldown"
            action = "limit_new_entries"
            reason = "Recovery cooldown is still active."

        else:
            status = "normal"
            action = "no_recovery_action"
            reason = "Drawdown is within the permitted range."

        result = {
            "timestamp": self._timestamp(),
            "mode": self.mode,
            "cycle": self.current_cycle,
            "drawdown_pct": drawdown,
            "status": status,
            "action": action,
            "reason": reason,
            "recovery_active": self.recovery_active,
            "emergency_stop": self.emergency_stop,
            "order_submitted": False,
        }

        self.history.append(result)
        return result

    def activate_emergency_stop(self, reason: str = "Manual safety stop") -> Dict[str, Any]:
        """Activate a simulation safety stop."""
        self.emergency_stop = True
        self.recovery_active = True

        event = {
            "timestamp": self._timestamp(),
            "mode": self.mode,
            "cycle": self.current_cycle,
            "event": "emergency_stop_activated",
            "reason": str(reason),
            "order_submitted": False,
        }

        self.history.append(event)
        return event

    def reset_emergency_stop(self) -> Dict[str, Any]:
        """Reset the safety stop for a new paper/testnet session."""
        self.emergency_stop = False

        event = {
            "timestamp": self._timestamp(),
            "mode": self.mode,
            "cycle": self.current_cycle,
            "event": "emergency_stop_reset",
            "order_submitted": False,
        }

        self.history.append(event)
        return event

    def get_status(self) -> Dict[str, Any]:
        """Return the current recovery-controller state."""
        return {
            "mode": self.mode,
            "current_cycle": self.current_cycle,
            "max_drawdown_pct": self.max_drawdown_pct,
            "recovery_target_pct": self.recovery_target_pct,
            "cooldown_cycles": self.cooldown_cycles,
            "last_recovery_cycle": self.last_recovery_cycle,
            "recovery_active": self.recovery_active,
            "emergency_stop": self.emergency_stop,
            "history_count": len(self.history),
            "real_trading_enabled": False,
        }
