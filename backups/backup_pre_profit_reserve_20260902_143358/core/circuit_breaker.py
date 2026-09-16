from datetime import datetime, timezone
from typing import Dict, Any, Optional


class CircuitBreaker:
    """
    Automated safety mechanism to halt trading operations during extreme volatility,
    consecutive execution failures, or severe drawdown spikes.
    """
    def __init__(
        self,
        max_consecutive_failures: int = 3,
        max_drawdown_pct_halt: float = 0.05,
        cooldown_seconds: float = 300.0,
        volatility_threshold_pct: float = 0.08
    ):
        if max_consecutive_failures <= 0:
            raise ValueError("max_consecutive_failures must be strictly positive")
        if max_drawdown_pct_halt <= 0.0:
            raise ValueError("max_drawdown_pct_halt must be strictly positive")

        self.max_consecutive_failures = max_consecutive_failures
        self.max_drawdown_pct_halt = max_drawdown_pct_halt
        self.cooldown_seconds = cooldown_seconds
        self.volatility_threshold_pct = volatility_threshold_pct

        self._consecutive_failures = 0
        self._is_halted = False
        self._halt_reason: Optional[str] = None
        self._halt_timestamp: Optional[datetime] = None

    @property
    def is_halted(self) -> bool:
        if not self._is_halted:
            return False
        # Check if cooldown period has elapsed
        if self._halt_timestamp and self.cooldown_seconds > 0:
            now = datetime.now(timezone.utc)
            elapsed = (now - self._halt_timestamp).total_seconds()
            if elapsed >= self.cooldown_seconds:
                self.reset(manual=False)
                return False
        return self._is_halted

    @property
    def halt_reason(self) -> Optional[str]:
        return self._halt_reason

    def record_execution_result(self, success: bool, error_message: Optional[str] = None) -> None:
        """Records order execution outcome and triggers halt if failure threshold is reached."""
        if success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.max_consecutive_failures:
                self._trigger_halt(f"Consecutive execution failures exceeded ({self._consecutive_failures}): {error_message or 'Unknown'}")

    def evaluate_market_conditions(self, price_change_pct: float, current_drawdown_pct: float) -> bool:
        """
        Evaluates real-time price volatility and current drawdown.
        Returns True if trading is safe (not halted), False if halted.
        """
        if abs(price_change_pct) >= self.volatility_threshold_pct:
            self._trigger_halt(f"Extreme market volatility detected: {price_change_pct * 100:.2f}%")
            return False

        if current_drawdown_pct >= self.max_drawdown_pct_halt:
            self._trigger_halt(f"Emergency drawdown limit hit: {current_drawdown_pct * 100:.2f}%")
            return False

        return not self.is_halted

    def _trigger_halt(self, reason: str) -> None:
        self._is_halted = True
        self._halt_reason = reason
        self._halt_timestamp = datetime.now(timezone.utc)

    def reset(self, manual: bool = True) -> None:
        """Resets the circuit breaker state to normal operation."""
        self._is_halted = False
        self._halt_reason = None
        self._halt_timestamp = None
        self._consecutive_failures = 0

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_halted": self.is_halted,
            "halt_reason": self._halt_reason,
            "consecutive_failures": self._consecutive_failures,
            "halt_timestamp": self._halt_timestamp.isoformat() if self._halt_timestamp else None,
            "max_consecutive_failures": self.max_consecutive_failures,
            "max_drawdown_pct_halt": self.max_drawdown_pct_halt,
            "volatility_threshold_pct": self.volatility_threshold_pct
        }
