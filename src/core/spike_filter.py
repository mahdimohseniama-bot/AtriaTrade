"""
Spike and Bad-Tick Filter for AtriaTrade (Capability 79).
Rejects abnormal outlier price ticks and flash spikes to prevent premature trigger executions.
"""

from typing import List, Dict, Any, Optional
import statistics


class SpikeFilter:
    def __init__(self, window_size: int = 5, max_deviation_pct: float = 0.05, confirmation_count: int = 2):
        """
        :param window_size: Number of recent prices to maintain rolling window.
        :param max_deviation_pct: Maximum allowed deviation from median (e.g. 0.05 = 5%).
        :param confirmation_count: Consecutive ticks required to accept a major jump as real.
        """
        self.window_size = window_size
        self.max_deviation_pct = max_deviation_pct
        self.confirmation_count = confirmation_count
        self.price_history: List[float] = []
        self.pending_outlier_count: int = 0
        self.last_valid_price: Optional[float] = None

    def process_tick(self, raw_price: float) -> Dict[str, Any]:
        """
        Filters incoming tick price.
        Returns whether the tick is valid and the sanitized price.
        """
        if raw_price <= 0:
            return {
                "is_valid": False,
                "sanitized_price": self.last_valid_price or 0.0,
                "reason": "INVALID_NON_POSITIVE_PRICE"
            }

        if not self.price_history:
            self.price_history.append(raw_price)
            self.last_valid_price = raw_price
            return {
                "is_valid": True,
                "sanitized_price": raw_price,
                "reason": "INITIAL_TICK"
            }

        # Calculate median of recent window
        median_price = statistics.median(self.price_history)
        deviation = abs(raw_price - median_price) / median_price

        if deviation > self.max_deviation_pct:
            self.pending_outlier_count += 1
            if self.pending_outlier_count >= self.confirmation_count:
                # Confirmed trend / real breakout
                self._update_window(raw_price)
                self.pending_outlier_count = 0
                self.last_valid_price = raw_price
                return {
                    "is_valid": True,
                    "sanitized_price": raw_price,
                    "reason": "CONFIRMED_BREAKOUT"
                }
            else:
                # Rejected as potential spike
                return {
                    "is_valid": False,
                    "sanitized_price": self.last_valid_price,
                    "reason": f"SPIKE_REJECTED_DEV_{deviation:.4f}"
                }
        else:
            self.pending_outlier_count = 0
            self._update_window(raw_price)
            self.last_valid_price = raw_price
            return {
                "is_valid": True,
                "sanitized_price": raw_price,
                "reason": "NORMAL_TICK"
            }

    def _update_window(self, price: float):
        self.price_history.append(price)
        if len(self.price_history) > self.window_size:
            self.price_history.pop(0)
