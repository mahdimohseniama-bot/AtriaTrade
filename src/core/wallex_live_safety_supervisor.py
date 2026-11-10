import time
from typing import Dict, Any, Optional

class WallexLiveSafetySupervisor:
    """
    Supervises live runtime health, recurring heartbeats, drift triggers,
    and automatic emergency halt engagements.
    """
    def __init__(self, orchestrator, heartbeat_timeout_sec: float = 30.0, max_heartbeat_misses: int = 3):
        self.orchestrator = orchestrator
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.max_heartbeat_misses = max_heartbeat_misses
        self.last_heartbeat_ts: float = time.time()
        self.missed_heartbeats: int = 0
        self.supervisor_active: bool = True

    def record_heartbeat(self, timestamp: Optional[float] = None) -> None:
        self.last_heartbeat_ts = timestamp if timestamp is not None else time.time()
        self.missed_heartbeats = 0

    def evaluate_health(self, current_ts: Optional[float] = None) -> Dict[str, Any]:
        now = current_ts if current_ts is not None else time.time()
        elapsed = now - self.last_heartbeat_ts

        if elapsed > self.heartbeat_timeout_sec:
            misses = int(elapsed // self.heartbeat_timeout_sec)
            self.missed_heartbeats = misses
            if self.missed_heartbeats >= self.max_heartbeat_misses:
                self.orchestrator.emergency_mgr.trigger_emergency_halt(
                    f"HEARTBEAT_TIMEOUT_MISSED_{self.missed_heartbeats}_INTERVALS"
                )
                return {
                    "healthy": False,
                    "status": "EMERGENCY_HALTED",
                    "missed_heartbeats": self.missed_heartbeats,
                    "elapsed_sec": round(elapsed, 2)
                }
            return {
                "healthy": False,
                "status": "HEARTBEAT_WARNING",
                "missed_heartbeats": self.missed_heartbeats,
                "elapsed_sec": round(elapsed, 2)
            }

        return {
            "healthy": True,
            "status": "HEALTHY",
            "missed_heartbeats": 0,
            "elapsed_sec": round(elapsed, 2)
        }

    def trigger_periodic_drift_scan(self, local_positions: Dict[str, float], exchange_positions: Dict[str, float]) -> Dict[str, Any]:
        drift_result = self.orchestrator.reconciler.reconcile(local_positions, exchange_positions)
        if drift_result.get("has_drift", False):
            self.orchestrator.emergency_mgr.trigger_emergency_halt("SUPERVISOR_DETECTED_POSITION_DRIFT")
            return {"status": "DRIFT_BREACH", "details": drift_result}
        return {"status": "IN_SYNC", "details": drift_result}
