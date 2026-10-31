import time
import logging
from typing import Dict, Any

logger = logging.getLogger("AtriaTrade.WallexRateLimiter")

class WallexRateLimiter:
    def __init__(self, max_requests_per_minute: int = 60, burst_limit: int = 10):
        self.max_requests_per_minute = max_requests_per_minute
        self.burst_limit = burst_limit
        self.tokens = float(burst_limit)
        self.fill_rate = max_requests_per_minute / 60.0  # tokens per second
        self.last_update = time.time()
        self.consecutive_429 = 0

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(float(self.burst_limit), self.tokens + elapsed * self.fill_rate)
        self.last_update = now

    def acquire(self, tokens: float = 1.0) -> bool:
        """
        Attempts to consume tokens. Returns True if allowed, False if throttled.
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        logger.warning(f"Rate limit exceeded: available={self.tokens:.2f}, requested={tokens}")
        return False

    def handle_response_code(self, status_code: int) -> Dict[str, Any]:
        """
        Inspects HTTP response codes to trigger adaptive backoff if 429 Too Many Requests occurs.
        """
        if status_code == 429:
            self.consecutive_429 += 1
            self.tokens = 0.0  # Deplete bucket immediately
            backoff_sec = min(60.0, (2 ** self.consecutive_429) * 1.5)
            logger.error(f"HTTP 429 received. Backoff required: {backoff_sec:.1f}s")
            return {"throttled": True, "backoff_seconds": backoff_sec}
        else:
            if self.consecutive_429 > 0 and status_code < 400:
                self.consecutive_429 = 0
            return {"throttled": False, "backoff_seconds": 0.0}
