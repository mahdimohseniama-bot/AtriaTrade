import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger("LiveCircuitBreakerEmergencyManager")

class LiveCircuitBreakerEmergencyManager:
    def __init__(
        self,
        max_daily_loss_pct: float = 0.03,
        max_consecutive_errors: int = 3
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_errors = max_consecutive_errors
        self.consecutive_errors = 0
        self.is_halted = False
        self.halt_reason: Optional[str] = None

    def record_success(self) -> None:
        """Resets the consecutive error counter upon successful execution."""
        self.consecutive_errors = 0

    def record_error(self, reason: str = "EXCHANGE_ERROR") -> bool:
        """
        Increments consecutive errors and trips breaker if limit is reached.
        Returns True if emergency halt is triggered.
        """
        self.consecutive_errors += 1
        logger.warning(
            f"Execution error recorded ({self.consecutive_errors}/{self.max_consecutive_errors}): {reason}"
        )
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.trigger_emergency_halt(f"EXCESSIVE_CONSECUTIVE_ERRORS: {reason}")
            return True
        return False

    def evaluate_daily_drawdown(self, starting_balance: float, current_balance: float) -> bool:
        """
        Evaluates daily drawdown percentage. If it exceeds max_daily_loss_pct, trips breaker.
        """
        if starting_balance <= 0:
            return False
        drawdown_pct = (starting_balance - current_balance) / starting_balance
        if drawdown_pct >= self.max_daily_loss_pct:
            self.trigger_emergency_halt(
                f"MAX_DAILY_DRAWDOWN_EXCEEDED: {drawdown_pct * 100:.2f}% >= {self.max_daily_loss_pct * 100:.2f}%"
            )
            return True
        return False

    def trigger_emergency_halt(self, reason: str, cancel_all_func: Optional[Callable[[], Any]] = None) -> Dict[str, Any]:
        """
        Triggers emergency halt and optionally executes cancel-all routine.
        """
        self.is_halted = True
        self.halt_reason = reason
        logger.critical(f"EMERGENCY CIRCUIT BREAKER TRIPPED: {reason}")

        cancelled = False
        if cancel_all_func:
            try:
                cancel_all_func()
                cancelled = True
                logger.info("Emergency cancel-all executed successfully.")
            except Exception as e:
                logger.error(f"Failed to execute emergency cancel-all: {e}")

        return {
            "halted": True,
            "reason": self.halt_reason,
            "orders_cancelled": cancelled
        }

    def can_trade(self) -> Dict[str, Any]:
        """Checks if trading is permitted."""
        return {
            "permitted": not self.is_halted,
            "reason": self.halt_reason if self.is_halted else None
        }

    def reset(self) -> None:
        """Resets the emergency manager state."""
        self.is_halted = False
        self.halt_reason = None
        self.consecutive_errors = 0
        logger.info("Emergency breaker state reset.")
