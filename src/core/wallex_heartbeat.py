import time
import logging
from typing import Dict, Any

logger = logging.getLogger("AtriaTrade.WallexHeartbeat")

class WallexHeartbeatMonitor:
    def __init__(self, exchange_adapter: Any, max_latency_ms: float = 1500.0, max_consecutive_drops: int = 3):
        self.adapter = exchange_adapter
        self.max_latency_ms = max_latency_ms
        self.max_consecutive_drops = max_consecutive_drops
        self.consecutive_drops = 0
        self.last_latency_ms = 0.0
        self.last_check_timestamp = 0.0

    def ping(self) -> Dict[str, Any]:
        """
        Pings exchange endpoint or checks market status to measure latency.
        Transitions into degraded/unhealthy status if latency exceeds thresholds.
        """
        start_time = time.perf_counter()
        try:
            # We call ping or get_status on adapter
            if hasattr(self.adapter, "ping"):
                alive = bool(self.adapter.ping())
            elif hasattr(self.adapter, "get_status"):
                status_res = self.adapter.get_status()
                alive = bool(status_res.get("status") in ("ok", "success", True))
            else:
                # Fallback probe
                alive = bool(self.adapter.get_orderbook(symbol="BTCUSDT"))
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self.last_latency_ms = latency_ms
            self.last_check_timestamp = time.time()

            if not alive:
                self.consecutive_drops += 1
                logger.warning(f"Heartbeat probe returned false. Drops: {self.consecutive_drops}")
                return {
                    "is_healthy": False,
                    "latency_ms": latency_ms,
                    "reason": "endpoint_unresponsive",
                    "consecutive_drops": self.consecutive_drops
                }

            if latency_ms > self.max_latency_ms:
                self.consecutive_drops += 1
                logger.warning(f"High latency detected: {latency_ms:.1f}ms > {self.max_latency_ms}ms")
                return {
                    "is_healthy": False,
                    "latency_ms": latency_ms,
                    "reason": "high_latency",
                    "consecutive_drops": self.consecutive_drops
                }

            # Reset drop count on healthy beat
            self.consecutive_drops = 0
            return {
                "is_healthy": True,
                "latency_ms": latency_ms,
                "reason": "normal",
                "consecutive_drops": 0
            }

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self.consecutive_drops += 1
            logger.error(f"Heartbeat probe failed: {e}")
            return {
                "is_healthy": False,
                "latency_ms": latency_ms,
                "reason": f"exception: {str(e)}",
                "consecutive_drops": self.consecutive_drops
            }

    def should_pause_trading(self) -> bool:
        """Returns True if connection drops exceed the tolerance threshold."""
        return self.consecutive_drops >= self.max_consecutive_drops
