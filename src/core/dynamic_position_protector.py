import logging
from typing import Optional

logger = logging.getLogger("dynamic_position_protector")

class DynamicPositionProtector:
    """
    Manages active position stop-loss and take-profit evaluations.
    """
    def __init__(self, tp_pct: float = 0.03, sl_pct: float = 0.015):
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.active = False
        self.entry_price = 0.0
        self.position_size = 0.0

    def open_position(self, entry_price: float, size: float):
        self.entry_price = float(entry_price)
        self.position_size = float(size)
        self.active = True
        logger.info(f"Position opened at {self.entry_price} with size {self.position_size}")

    def close_position(self):
        logger.info(f"Position closed. Previous entry: {self.entry_price}")
        self.active = False
        self.entry_price = 0.0
        self.position_size = 0.0

    def has_active_position(self) -> bool:
        return self.active

    def evaluate(self, current_price: float) -> str:
        if not self.active or self.entry_price <= 0:
            return "HOLD"

        price = float(current_price)
        tp_target = self.entry_price * (1.0 + self.tp_pct)
        sl_target = self.entry_price * (1.0 - self.sl_pct)

        if price >= tp_target:
            return "TP"
        elif price <= sl_target:
            return "SL"
        return "HOLD"
