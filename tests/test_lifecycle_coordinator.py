import time
from src.core.lifecycle_coordinator import LifecycleCoordinator, SystemState


def test_initial_state_and_transitions():
    coordinator = LifecycleCoordinator()
    assert coordinator.state == SystemState.IDLE

    assert coordinator.start() is True
    assert coordinator.state == SystemState.RUNNING

    assert coordinator.pause(reason="Maintenance") is True
    assert coordinator.state == SystemState.PAUSED

    assert coordinator.start() is True
    assert coordinator.state == SystemState.RUNNING

    assert coordinator.stop() is True
    assert coordinator.state == SystemState.IDLE


def test_critical_error_and_shutdown():
    coordinator = LifecycleCoordinator()
    coordinator.start()

    coordinator.trigger_critical_error("Memory exhausted")
    assert coordinator.state == SystemState.CRITICAL_ERROR
    assert coordinator.get_health_status()["is_healthy"] is False

    coordinator.shutdown("Emergency shutdown")
    assert coordinator.state == SystemState.SHUTDOWN
    assert coordinator.start() is False


def test_component_heartbeat_and_stale_detection():
    coordinator = LifecycleCoordinator(heartbeat_timeout_sec=0.05)
    coordinator.start()

    coordinator.ping_component("OrderExecutor")
    coordinator.ping_component("RiskManager")

    health = coordinator.get_health_status()
    assert health["is_healthy"] is True
    assert len(health["stale_components"]) == 0

    # Wait until timeout expires
    time.sleep(0.06)

    # Refresh only RiskManager
    coordinator.ping_component("RiskManager")

    health = coordinator.get_health_status()
    assert health["is_healthy"] is False
    assert "OrderExecutor" in health["stale_components"]
    assert "RiskManager" not in health["stale_components"]
