import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("alert_notifier")

class AlertNotifier:
    """
    Lightweight resilient notifier designed for Iranian network context.
    Safely degrades to structured console logging when external APIs are unreachable.
    """
    def __init__(self, telegram_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.enabled = bool(telegram_token and chat_id)
        self.history = []

    def notify(self, title: str, message: str, level: str = "INFO", meta: Optional[Dict[str, Any]] = None) -> bool:
        record = {
            "title": title,
            "message": message,
            "level": level.upper(),
            "meta": meta or {}
        }
        self.history.append(record)
        
        # Structured terminal fallback log
        log_msg = f"[{record['level']}] {record['title']}: {record['message']} | Meta: {record['meta']}"
        if record["level"] in ["ERROR", "CRITICAL"]:
            logger.error(log_msg)
        elif record["level"] == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # In case telegram credentials are provided, attempts can be staged here.
        # Defaults to local safe delivery.
        return True

    def get_last_alert(self) -> Optional[Dict[str, Any]]:
        return self.history[-1] if self.history else None
