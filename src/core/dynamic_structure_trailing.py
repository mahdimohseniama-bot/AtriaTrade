"""
ATR and Market Structure Dynamic Trailing Stop Engine for AtriaTrade (Capability 77).
Locks in profits dynamically using volatility (ATR) or market swing points.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TrailingState:
    symbol: str
    direction: str  # "BUY" or "SELL"
    current_sl: float
    highest_price: float
    lowest_price: float
    atr_multiplier: float = 2.0
    buffer_percent: float = 0.001


class DynamicStructureTrailing:
    def __init__(self, mode: str = "ATR"):
        """
        mode: "ATR" or "STRUCTURE"
        """
        self.mode = mode.upper()

    def update_trailing_stop(
        self,
        state: TrailingState,
        current_high: float,
        current_low: float,
        current_atr: Optional[float] = None,
        swing_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Updates the stop loss based on new price action.
        Guarantees ratchet behavior (SL only moves in favorable direction).
        """
        is_buy = state.direction.upper() == "BUY"
        old_sl = state.current_sl
        moved = False

        if is_buy:
            if current_high > state.highest_price:
                state.highest_price = current_high

            if self.mode == "ATR" and current_atr is not None and current_atr > 0:
                proposed_sl = state.highest_price - (current_atr * state.atr_multiplier)
            elif self.mode == "STRUCTURE" and swing_level is not None:
                proposed_sl = swing_level * (1.0 - state.buffer_percent)
            else:
                proposed_sl = old_sl

            # Ratchet logic: SL can only increase for BUY
            if proposed_sl > state.current_sl:
                state.current_sl = round(proposed_sl, 4)
                moved = True

        else:  # SELL
            if current_low < state.lowest_price:
                state.lowest_price = current_low

            if self.mode == "ATR" and current_atr is not None and current_atr > 0:
                proposed_sl = state.lowest_price + (current_atr * state.atr_multiplier)
            elif self.mode == "STRUCTURE" and swing_level is not None:
                proposed_sl = swing_level * (1.0 + state.buffer_percent)
            else:
                proposed_sl = old_sl

            # Ratchet logic: SL can only decrease for SELL
            if proposed_sl < state.current_sl:
                state.current_sl = round(proposed_sl, 4)
                moved = True

        return {
            "symbol": state.symbol,
            "direction": state.direction,
            "old_sl": old_sl,
            "new_sl": state.current_sl,
            "trail_moved": moved,
            "highest_price": state.highest_price,
            "lowest_price": state.lowest_price
        }
