import time
from typing import Any, Callable, Dict, Optional, Tuple
from src.core.network_health_monitor import NetworkHealthMonitor

class SafeExchangeCaller:
    def __init__(self, monitor: NetworkHealthMonitor):
        self.monitor = monitor

    def execute(self, action_name: str, func: Callable[..., Any], *args, **kwargs) -> Tuple[bool, Optional[Any], Optional[str]]:
        """
        Executes a network-dependent exchange function safely.
        Returns: (success: bool, result: Optional[Any], error_message: Optional[str])
        """
        if not self.monitor.is_operation_permitted():
            error_msg = f"Operation '{action_name}' rejected: Network circuit breaker is active."
            return False, None, error_msg

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.monitor.record_success(elapsed_ms)
            return True, result, None
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"{action_name} failed: {str(exc)}"
            self.monitor.record_failure(err_msg)
            return False, None, err_msg
