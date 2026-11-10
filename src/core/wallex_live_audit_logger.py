import os
import json
import time
from typing import Dict, Any, Optional

class WallexLiveAuditLogger:
    """
    Structured append-only audit logger for live trading operations,
    pre-flight safety checks, and emergency breaker events.
    """
    def __init__(self, log_dir: str = "logs", filename: str = "wallex_live_audit.jsonl"):
        self.log_dir = log_dir
        self.filepath = os.path.join(self.log_dir, filename)
        os.makedirs(self.log_dir, exist_ok=True)

    def log_event(self, event_type: str, payload: Dict[str, Any], status: str = "INFO", timestamp: Optional[float] = None) -> Dict[str, Any]:
        ts = timestamp if timestamp is not None else time.time()
        record = {
            "timestamp": ts,
            "event_type": event_type,
            "status": status,
            "payload": payload
        }
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(',', ':')) + "\n")
        return record

    def read_recent_events(self, limit: int = 10) -> list:
        if not os.path.exists(self.filepath):
            return []
        events = []
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events[-limit:]
