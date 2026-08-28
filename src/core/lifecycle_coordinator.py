import time
from typing import Dict, Any, Optional
from enum import Enum


class SystemState(str, Enum):
    BOOTING = "BOOTING"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    SHUTDOWN = "SHUTDOWN"


class LifecycleCoordinator:
    """
    Coordinates bot lifecycle states, component heartbeats, and system health status.
    """
    def __init__(self, heartbeat_timeout_sec: float = 30.0):
        self.state: SystemState = SystemState.BOOTING
        self.heartbeat_timeout_sec: float = heartbeat_timeout_sec
        self._component_heartbeats: Dict[str, float] = {}
        self._metadata: Dict[str, Any] = {}
        self._state_history = []
        self._transition_to(SystemState.IDLE, reason="Initial bootstrap complete")

    def _transition_to(self, new_state: SystemState, reason: str = "") -> None:
        old_state = getattr(self, "state", None)
        self.state = new_state
        self._state_history.append({
            "from": old_state.value if old_state else None,
            "to": new_state.value,
            "timestamp": time.time(),
            "reason": reason
        })

    def start(self) -> bool:
        """Transitions bot to RUNNING if IDLE or PAUSED."""
        if self.state in (SystemState.IDLE, SystemState.PAUSED):
            self._transition_to(SystemState.RUNNING, reason="Manual start/resume")
            return True
        return False

    def pause(self, reason: str = "User requested pause") -> bool:
        """Transitions bot to PAUSED state."""
        if self.state == SystemState.RUNNING:
            self._transition_to(SystemState.PAUSED, reason=reason)
            return True
        return False

    def stop(self, reason: str = "User requested stop") -> bool:
        """Transitions bot to IDLE state."""
        if self.state in (SystemState.RUNNING, SystemState.PAUSED):
            self._transition_to(SystemState.IDLE, reason=reason)
            return True
        return False

    def shutdown(self, reason: str = "System shutdown initiated") -> None:
        """Permanently marks system as SHUTDOWN."""
        self._transition_to(SystemState.SHUTDOWN, reason=reason)

    def trigger_critical_error(self, reason: str) -> None:
        """Forces system into CRITICAL_ERROR state."""
        self._transition_to(SystemState.CRITICAL_ERROR, reason=reason)

    def ping_component(self, component_name: str) -> None:
        """Records a heartbeat timestamp for a given component."""
        self._component_heartbeats[component_name] = time.time()

    def get_health_status(self) -> Dict[str, Any]:
        """
        Calculates health metrics and identifies stale components.
        """
        now = time.time()
        stale_components = []

        for name, last_ping in self._component_heartbeats.items():
            if (now - last_ping) > self.heartbeat_timeout_sec:
                stale_components.append(name)

        is_healthy = (
            self.state not in (SystemState.CRITICAL_ERROR, SystemState.SHUTDOWN)
            and len(stale_components) == 0
        )

        return {
            "state": self.state.value,
            "is_healthy": is_healthy,
            "active_components": list(self._component_heartbeats.keys()),
            "stale_components": stale_components,
            "total_transitions": len(self._state_history),
            "last_transition": self._state_history[-1] if self._state_history else None
        }
