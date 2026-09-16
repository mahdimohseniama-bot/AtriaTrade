from typing import Dict, Any, Optional
import time


class SignalDedupCooldownManager:
    """
    Signal Deduplication and Cooldown Manager.
    Prevents duplicate entries on the same symbol/direction within cooldown periods.
    """
    def __init__(self, cooldown_seconds: float = 900.0):
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative.")
        self.cooldown_seconds = cooldown_seconds
        self._last_entry_time: Dict[tuple, float] = {}

    def is_duplicate(self, symbol: str, direction: str, now: Optional[float] = None) -> bool:
        """Check if an entry is duplicate due to active cooldown."""
        if direction not in ("BUY", "SELL"):
            raise ValueError(f"Invalid direction: {direction}")
        t = time.time() if now is None else now
        key = (symbol, direction)
        last = self._last_entry_time.get(key)
        if last is not None and (t - last) < self.cooldown_seconds:
            return True
        return False

    def register_entry(self, symbol: str, direction: str, now: Optional[float] = None) -> None:
        """Register a new entry and trigger cooldown timer."""
        if direction not in ("BUY", "SELL"):
            raise ValueError(f"Invalid direction: {direction}")
        t = time.time() if now is None else now
        self._last_entry_time[(symbol, direction)] = t

    def clear_entry(self, symbol: str, direction: str) -> None:
        """Manually clear cooldown record for a symbol and direction."""
        self._last_entry_time.pop((symbol, direction), None)

    def remaining_cooldown(self, symbol: str, direction: str, now: Optional[float] = None) -> float:
        """Return remaining cooldown seconds. Returns 0.0 if not on cooldown."""
        t = time.time() if now is None else now
        last = self._last_entry_time.get((symbol, direction))
        if last is None:
            return 0.0
        return max(0.0, round(self.cooldown_seconds - (t - last), 3))
