import time
from typing import Dict, Any, Optional

class WallexLiveSafetySupervisor:
    """
    Supervises live health, heartbeats, and balance drifts for Wallex live trading.
    """
    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        heartbeat_timeout_sec: float = 5.0,
        max_heartbeat_misses: int = 3,
        **kwargs
    ):
        self.orchestrator = orchestrator
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.max_heartbeat_misses = max_heartbeat_misses
        self.last_heartbeat = None
        self.missed_heartbeats = 0
        self.state = "INITIALIZING"

    def pulse_heartbeat(self, timestamp: Optional[float] = None) -> None:
        self.record_heartbeat(timestamp=timestamp)

    def record_heartbeat(self, timestamp: Optional[float] = None, current_time: Optional[float] = None) -> None:
        now = timestamp if timestamp is not None else (current_time if current_time is not None else time.time())
        self.last_heartbeat = now
        self.missed_heartbeats = 0
        self.state = "HEALTHY"

    def _trigger_emergency(self, reason: str) -> None:
        if self.orchestrator and hasattr(self.orchestrator, "emergency_mgr"):
            mgr = self.orchestrator.emergency_mgr
            if hasattr(mgr, "trigger_emergency_halt"):
                mgr.trigger_emergency_halt(reason)
            elif hasattr(mgr, "trigger_halt"):
                mgr.trigger_halt(reason)

    def evaluate_health(
        self,
        current_ts: Optional[float] = None,
        current_timestamp: Optional[float] = None,
        current_time: Optional[float] = None
    ) -> Dict[str, Any]:
        now = current_ts if current_ts is not None else (
            current_timestamp if current_timestamp is not None else (
                current_time if current_time is not None else time.time()
            )
        )

        if self.last_heartbeat is None:
            self.state = "UNHEALTHY_NO_PULSE"
            return {
                "healthy": False,
                "status": self.state,
                "state": self.state,
                "reason": "NO_HEARTBEAT_RECORDED",
                "missed_heartbeats": 999,
                "elapsed": 999.0
            }

        elapsed = now - self.last_heartbeat

        if elapsed > self.heartbeat_timeout_sec:
            misses = int(elapsed // self.heartbeat_timeout_sec)
            self.missed_heartbeats = misses
            if self.missed_heartbeats >= self.max_heartbeat_misses:
                self.state = "EMERGENCY_HALTED"
                self._trigger_emergency("MAX_HEARTBEAT_MISSES_EXCEEDED")
                return {
                    "healthy": False,
                    "status": "EMERGENCY_HALTED",
                    "state": "EMERGENCY_HALTED",
                    "reason": "MAX_HEARTBEAT_MISSES_EXCEEDED",
                    "missed_heartbeats": self.missed_heartbeats,
                    "elapsed": round(elapsed, 4)
                }
            else:
                self.state = "HEARTBEAT_WARNING"
                return {
                    "healthy": False,
                    "status": "HEARTBEAT_WARNING",
                    "state": "HEARTBEAT_WARNING",
                    "reason": "HEARTBEAT_TIMEOUT_EXCEEDED",
                    "missed_heartbeats": self.missed_heartbeats,
                    "elapsed": round(elapsed, 4)
                }

        self.missed_heartbeats = 0
        self.state = "HEALTHY"
        return {
            "healthy": True,
            "status": "HEALTHY",
            "state": "HEALTHY",
            "reason": "OK",
            "missed_heartbeats": 0,
            "elapsed": round(elapsed, 4)
        }

    def check_health(self, current_timestamp: Optional[float] = None, current_time: Optional[float] = None) -> Dict[str, Any]:
        return self.evaluate_health(current_timestamp=current_timestamp, current_time=current_time)

    def trigger_periodic_drift_scan(self, local_balances: Dict[str, Any], remote_balances: Dict[str, Any]) -> Dict[str, Any]:
        if self.orchestrator and hasattr(self.orchestrator, "reconciler"):
            res = self.orchestrator.reconciler.reconcile(local_balances, remote_balances)
            if res.get("has_drift", False):
                self.state = "DRIFT_BREACH"
                self._trigger_emergency("SUPERVISOR_DETECTED_POSITION_DRIFT")
                return {"action": "HALT_TRADING", "status": "DRIFT_BREACH", "details": res}
            return {"action": "CONTINUE", "status": "ALIGNED", "details": res}
        return {"action": "CONTINUE", "status": "NO_RECONCILER"}

    def run_drift_scan(self, balance_synced: bool, orders_synced: bool) -> Dict[str, Any]:
        if not balance_synced or not orders_synced:
            self.state = "DRIFT_BREACH"
            self._trigger_emergency("SUPERVISOR_DETECTED_POSITION_DRIFT")
            return {"action": "HALT_TRADING", "status": "DRIFT_BREACH", "reason": "DRIFT_DETECTED"}
        return {"action": "CONTINUE", "status": "ALIGNED", "reason": "SYSTEM_ALIGNED"}
