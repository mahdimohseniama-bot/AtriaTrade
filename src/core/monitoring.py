import logging
import os
import time
from enum import Enum
from typing import Dict, Any, List, Optional

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AtriaLogger:
    def __init__(self, name: str = "AtriaTrade", log_file: Optional[str] = None, level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.log_history: List[Dict[str, Any]] = []

        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")

        if not self.logger.handlers:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger

    def _record(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "context": context or {}
        }
        self.log_history.append(entry)

    def info(self, message: str, **kwargs):
        self._record("INFO", message, kwargs)
        self.logger.info(message)

    def warning(self, message: str, **kwargs):
        self._record("WARNING", message, kwargs)
        self.logger.warning(message)

    def error(self, message: str, **kwargs):
        self._record("ERROR", message, kwargs)
        self.logger.error(message)

    def critical(self, message: str, **kwargs):
        self._record("CRITICAL", message, kwargs)
        self.logger.critical(message)

    def debug(self, message: str, **kwargs):
        self._record("DEBUG", message, kwargs)
        self.logger.debug(message)

    def get_logs(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        if level is None:
            return self.log_history
        return [log for log in self.log_history if log["level"].upper() == level.upper()]

class SystemAlertManager:
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.logger = AtriaLogger("SystemAlertManager")

    def trigger_alert(self, *args, **kwargs):
        # Can be called as:
        # trigger_alert(AlertLevel.WARNING, "High Latency", "Network lag detected")
        # trigger_alert(title="...", message="...", level=AlertLevel.INFO, context=...)
        # trigger_alert("title", "message", AlertLevel.INFO)
        level = kwargs.get("level", AlertLevel.INFO)
        title = kwargs.get("title", "")
        message = kwargs.get("message", "")
        context = kwargs.get("context", {})

        if len(args) == 3:
            if isinstance(args[0], AlertLevel):
                level, title, message = args[0], str(args[1]), str(args[2])
            else:
                title, message, level = str(args[0]), str(args[1]), args[2]
        elif len(args) == 2:
            title, message = str(args[0]), str(args[1])
        elif len(args) == 1:
            message = str(args[0])

        alert = {
            "timestamp": time.time(),
            "title": title,
            "message": message,
            "level": level,
            "context": context
        }
        self.alerts.append(alert)
        log_msg = f"[{title}] {message} | Context: {context}"
        if level == AlertLevel.CRITICAL:
            self.logger.critical(log_msg)
        elif level == AlertLevel.ERROR:
            self.logger.error(log_msg)
        elif level == AlertLevel.WARNING:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

    def get_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        if level is None:
            return self.alerts
        return [a for a in self.alerts if a["level"] == level]

class SystemHealthMonitor:
    def __init__(self, alert_manager: Optional[SystemAlertManager] = None):
        self.alert_manager = alert_manager or SystemAlertManager()
        self.total_ticks_processed = 0
        self.error_count = 0
        self.status = "HEALTHY"

    def record_tick(self):
        self.total_ticks_processed += 1

    def record_error(self, error_message: str):
        self.error_count += 1
        if self.error_count > 5:
            self.status = "DEGRADED"
        self.alert_manager.trigger_alert(
            title="System Error Recorded",
            message=error_message,
            level=AlertLevel.ERROR,
            context={"error_count": self.error_count, "status": self.status}
        )

    def is_alive(self) -> bool:
        return self.status != "CRITICAL"

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_ticks": self.total_ticks_processed,
            "error_count": self.error_count,
            "is_alive": self.is_alive(),
            "active_alerts_count": len(self.alert_manager.get_alerts())
        }
