import time
import logging
from typing import Any, Callable, Dict, Optional
from src.core.network_health_monitor import NetworkHealthMonitor
from src.core.safe_exchange_caller import SafeExchangeCaller

logger = logging.getLogger("WallexResilientSession")

class WallexResilientSession:
    def __init__(
        self,
        network_monitor: Optional[NetworkHealthMonitor] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5
    ):
        self.monitor = network_monitor or NetworkHealthMonitor()
        self.caller = SafeExchangeCaller(self.monitor)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def request_with_retry(
        self,
        endpoint_name: str,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes a network call with exponential backoff and circuit breaking protection.
        """
        attempt = 0
        last_error = "Unknown error"

        while attempt < self.max_retries:
            attempt += 1
            success, result, error = self.caller.execute(
                f"{endpoint_name}_attempt_{attempt}",
                func,
                *args,
                **kwargs
            )
            if success:
                return {
                    "success": True,
                    "data": result,
                    "attempts": attempt,
                    "error": None
                }
            
            last_error = error or "Execution failed"
            # If circuit breaker is broken, stop retrying immediately to preserve rate limits
            if not self.monitor.is_operation_permitted():
                break

            if attempt < self.max_retries:
                sleep_duration = self.backoff_factor * (2 ** (attempt - 1))
                time.sleep(sleep_duration)

        return {
            "success": False,
            "data": None,
            "attempts": attempt,
            "error": last_error
        }
