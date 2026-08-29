"""
Killzone and Trading Session Filter for AtriaTrade (Capability 73).
Identifies smart money trading sessions and validates trade timing.
"""

from dataclasses import dataclass
from datetime import datetime, time, timezone
from enum import Enum
from typing import Optional, Tuple


class SessionType(str, Enum):
    ASIA_ACCUMULATION = "ASIA_ACCUMULATION"
    LONDON_OPEN = "LONDON_OPEN"
    NY_OPEN_AM = "NY_OPEN_AM"
    NY_PM_REVERSAL = "NY_PM_REVERSAL"
    LONDON_CLOSE = "LONDON_CLOSE"
    OUT_OF_SESSION = "OUT_OF_SESSION"


@dataclass(frozen=True)
class SessionWindow:
    name: SessionType
    start_utc: time
    end_utc: time
    is_killzone: bool


class KillzoneFilter:
    """
    Evaluates current time against institutional killzones (UTC timezone).
    """

    # استاندارد سشن‌ها و کیل‌زون‌های ICT بر مبنای ساعت جهانی (UTC)
    SESSION_WINDOWS = [
        SessionWindow(SessionType.ASIA_ACCUMULATION, time(0, 0), time(4, 0), is_killzone=False),
        SessionWindow(SessionType.LONDON_OPEN, time(7, 0), time(10, 0), is_killzone=True),
        SessionWindow(SessionType.NY_OPEN_AM, time(12, 0), time(15, 0), is_killzone=True),
        SessionWindow(SessionType.LONDON_CLOSE, time(15, 0), time(17, 0), is_killzone=True),
        SessionWindow(SessionType.NY_PM_REVERSAL, time(18, 0), time(20, 0), is_killzone=False),
    ]

    def get_current_session(self, current_dt: Optional[datetime] = None) -> Tuple[SessionType, bool]:
        """
        تشخیص سشن معاملاتی فعلی و وضعیت کیل‌زون بودن آن.
        """
        if current_dt is None:
            current_dt = datetime.now(timezone.utc)
        
        target_time = current_dt.timetz() if current_dt.tzinfo else current_dt.time()
        # مقایسه فقط بر اساس time
        eval_time = current_dt.time()

        for window in self.SESSION_WINDOWS:
            if window.start_utc <= eval_time < window.end_utc:
                return window.name, window.is_killzone

        return SessionType.OUT_OF_SESSION, False

    def is_valid_killzone_entry(self, current_dt: Optional[datetime] = None, allow_asia: bool = False) -> bool:
        """
        اعتبارسنجی ورود به معامله در بازه‌های زمانی پرنقدینگی و سازمانی.
        """
        session, is_killzone = self.get_current_session(current_dt)

        if is_killzone:
            return True
        
        if allow_asia and session == SessionType.ASIA_ACCUMULATION:
            return True

        return False
