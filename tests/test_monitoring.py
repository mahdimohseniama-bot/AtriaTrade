import pytest
import time
from src.core.monitoring import SystemAlertManager, SystemHealthMonitor, AlertLevel

def test_alert_manager_trigger_and_filter():
    am = SystemAlertManager()
    am.trigger_alert(AlertLevel.INFO, "Test Info", "Information message")
    am.trigger_alert(AlertLevel.CRITICAL, "Emergency", "Margin call risk", {"loss": -150})
    
    all_alerts = am.get_alerts()
    assert len(all_alerts) == 2
    
    crit_alerts = am.get_alerts(level=AlertLevel.CRITICAL)
    assert len(crit_alerts) == 1
    assert crit_alerts[0]["title"] == "Emergency"
    assert crit_alerts[0]["context"]["loss"] == -150

def test_health_monitor_metrics_and_status():
    am = SystemAlertManager()
    monitor = SystemHealthMonitor(alert_manager=am)
    
    # ثبت تیک
    monitor.record_tick()
    assert monitor.total_ticks_processed == 1
    
    # بررسی سلامت اولیه
    health = monitor.get_health_status()
    assert health["status"] == "HEALTHY"
    assert health["is_alive"] is True
    assert health["error_count"] == 0

    # ثبت خطا و کاهش درجه سلامت
    for i in range(6):
        monitor.record_error(f"Error {i}")
        
    health_after_errors = monitor.get_health_status()
    assert health_after_errors["status"] == "DEGRADED"
    assert health_after_errors["error_count"] == 6
    assert len(am.get_alerts(level=AlertLevel.ERROR)) == 6
