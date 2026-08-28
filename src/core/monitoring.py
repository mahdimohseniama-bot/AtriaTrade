import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SystemAlertManager:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []

    def trigger_alert(self, level: AlertLevel, title: str, message: str, context: Optional[Dict[str, Any]] = None):
        alert_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "title": title,
            "message": message,
            "context": context or {}
        }
        self.alerts.append(alert_entry)
        log_msg = f"[{level.value}] {title}: {message}"
        if level in (AlertLevel.ERROR, AlertLevel.CRITICAL):
            logging.error(log_msg)
        elif level == AlertLevel.WARNING:
            logging.warning(log_msg)
        else:
            logging.info(log_msg)
        return alert_entry

    def get_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        if level:
            return [a for a in self.alerts if a["level"] == level.value]
        return self.alerts

class SystemHealthMonitor:
    def __init__(self, alert_manager: Optional[SystemAlertManager] = None):
        self.alert_manager = alert_manager or SystemAlertManager()
        self.last_heartbeat: Optional[datetime] = None
        self.error_count: int = 0
        self.total_ticks_processed: int = 0

    def record_tick(self):
        self.total_ticks_processed += 1
        self.last_heartbeat = datetime.now(timezone.utc)

    def record_error(self, error_message: str):
        self.error_count += 1
        self.alert_manager.trigger_alert(
            AlertLevel.ERROR,
            "System Error Recorded",
            error_message,
            {"error_count": self.error_count}
        )

    def get_health_status(self) -> Dict[str, Any]:
        status = "HEALTHY"
        if self.error_count > 5:
            status = "DEGRADED"
        if self.error_count > 20:
            status = "UNHEALTHY"
        return {
            "status": status,
            "is_alive": True,
            "total_ticks": self.total_ticks_processed,
            "error_count": self.error_count,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
