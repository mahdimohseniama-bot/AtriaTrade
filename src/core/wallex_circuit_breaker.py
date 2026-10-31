import logging
import time
from typing import Dict, Any

logger = logging.getLogger("AtriaTrade.WallexCircuitBreaker")

class WallexCircuitBreaker:
    def __init__(self, max_consecutive_errors: int = 3, cooldown_seconds: float = 60.0):
        self.max_consecutive_errors = max_consecutive_errors
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False

    def record_success(self) -> None:
        """Reset consecutive failures on a successful interaction."""
        self.failure_count = 0
        self.is_open = False

    def record_failure(self, error_msg: str = "") -> None:
        """Record API or execution error and trip if limit reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"Recorded failure ({self.failure_count}/{self.max_consecutive_errors}): {error_msg}")
        if self.failure_count >= self.max_consecutive_errors:
            self.is_open = True
            logger.critical("WallexCircuitBreaker TRIPPED! Trading execution halted.")

    def can_execute(self) -> bool:
        """Check if executions are currently permitted."""
        if not self.is_open:
            return True
        
        # Check if cooldown has elapsed for auto-half-open probe
        elapsed = time.time() - self.last_failure_time
        if elapsed >= self.cooldown_seconds:
            logger.info("Cooldown elapsed. Transitioning to probe state.")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "can_execute": self.can_execute()
        }
