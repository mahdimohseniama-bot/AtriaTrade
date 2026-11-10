import time
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class HealthStatus:
    is_healthy: bool
    consecutive_failures: int
    avg_latency_ms: float
    last_error: Optional[str] = None
    is_circuit_broken: bool = False

class NetworkHealthMonitor:
    def __init__(
        self,
        max_consecutive_failures: int = 3,
        latency_threshold_ms: float = 3000.0,
        circuit_cooldown_seconds: float = 60.0
    ):
        self.max_consecutive_failures = max_consecutive_failures
        self.latency_threshold_ms = latency_threshold_ms
        self.circuit_cooldown_seconds = circuit_cooldown_seconds

        self.consecutive_failures: int = 0
        self.recent_latencies: List[float] = []
        self.last_error: Optional[str] = None
        self.circuit_broken_until: float = 0.0

    def record_success(self, latency_ms: float) -> None:
        self.consecutive_failures = 0
        self.last_error = None
        self.recent_latencies.append(latency_ms)
        if len(self.recent_latencies) > 20:
            self.recent_latencies.pop(0)

    def record_failure(self, error_message: str) -> None:
        self.consecutive_failures += 1
        self.last_error = error_message
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.circuit_broken_until = time.time() + self.circuit_cooldown_seconds

    def is_operation_permitted(self) -> bool:
        return time.time() >= self.circuit_broken_until

    def get_status(self) -> HealthStatus:
        now = time.time()
        is_broken = now < self.circuit_broken_until
        avg_lat = (
            sum(self.recent_latencies) / len(self.recent_latencies)
            if self.recent_latencies else 0.0
        )
        is_healthy = (not is_broken) and (self.consecutive_failures == 0)
        return HealthStatus(
            is_healthy=is_healthy,
            consecutive_failures=self.consecutive_failures,
            avg_latency_ms=avg_lat,
            last_error=self.last_error,
            is_circuit_broken=is_broken
        )
