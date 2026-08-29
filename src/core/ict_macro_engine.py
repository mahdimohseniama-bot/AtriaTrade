"""
ICT Macro & Time-Window Liquidity Delivery Engine (Capability 95)
Identifies ICT Killzones and high-probability algorithmic Macro delivery windows
based on UTC/New York market time to filter trade timing.
"""

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import List, Optional


class WindowType(str, Enum):
    MACRO = "MACRO"
    KILLZONE = "KILLZONE"
    DEAD_ZONE = "DEAD_ZONE"


@dataclass
class TimeWindow:
    name: str
    window_type: WindowType
    start_time: time
    end_time: time
    weight_boost: float


class ICTMacroEngine:
    """
    Evaluates market time for ICT killzones, algorithmic macros, and liquidity windows.
    Times are handled natively in New York / EST standard time format (HH:MM).
    """

    def __init__(self):
        # Default standard ICT New York Macros
        self.windows: List[TimeWindow] = [
            # Killzones
            TimeWindow("Asian Killzone", WindowType.KILLZONE, time(20, 0), time(0, 0), 1.2),
            TimeWindow("London Open Killzone", WindowType.KILLZONE, time(2, 0), time(5, 0), 1.5),
            TimeWindow("NY Open Killzone", WindowType.KILLZONE, time(7, 0), time(10, 0), 1.6),
            TimeWindow("London Close Killzone", WindowType.KILLZONE, time(10, 0), time(12, 0), 1.3),
            
            # High-Impact Macros (Algorithmic Injections)
            TimeWindow("London 02:33 Macro", WindowType.MACRO, time(2, 33), time(3, 0), 1.8),
            TimeWindow("NY AM 08:50 Macro", WindowType.MACRO, time(8, 50), time(9, 10), 2.0),
            TimeWindow("NY AM 09:50 Macro", WindowType.MACRO, time(9, 50), time(10, 10), 2.0),
            TimeWindow("NY Lunch 11:50 Macro", WindowType.MACRO, time(11, 50), time(12, 10), 1.4),
            TimeWindow("NY PM 13:10 Macro", WindowType.MACRO, time(13, 10), time(13, 40), 1.7),
            TimeWindow("NY PM 15:15 Close Macro", WindowType.MACRO, time(15, 15), time(15, 45), 1.6),
        ]

    def _is_time_in_range(self, t: time, start: time, end: time) -> bool:
        """Helper to check if a time is within range, handling midnight wraparound."""
        if start <= end:
            return start <= t <= end
        else:
            # Over midnight (e.g. 20:00 to 00:00)
            return t >= start or t <= end

    def get_active_windows(self, current_time: time) -> List[TimeWindow]:
        """Returns all matching active ICT Killzones and Macros at given time."""
        active = []
        for win in self.windows:
            if self._is_time_in_range(current_time, win.start_time, win.end_time):
                active.append(win)
        return active

    def evaluate_timing_factor(self, current_time: time) -> float:
        """
        Calculates execution weight boost based on the most potent active window.
        Returns 1.0 (baseline) if no special window is active.
        """
        active = self.get_active_windows(current_time)
        if not active:
            return 1.0
        return max(win.weight_boost for win in active)

    def is_macro_active(self, current_time: time) -> bool:
        """True if an ICT Macro injection window is currently active."""
        active = self.get_active_windows(current_time)
        return any(win.window_type == WindowType.MACRO for win in active)
