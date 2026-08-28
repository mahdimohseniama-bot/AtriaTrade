from typing import Optional, Dict, Any


class DynamicTrailingStop:
    """
    Manages volatility-adjusted trailing stop losses for open positions.
    Supports Long and Short positions with ATR-based or percentage dynamic offsets.
    """
    def __init__(
        self,
        symbol: str,
        side: str,  # 'BUY' / 'LONG' or 'SELL' / 'SHORT'
        entry_price: float,
        activation_pct: float = 0.015,  # 1.5% profit before trailing starts
        atr_multiplier: float = 2.0,
        default_offset_pct: float = 0.01  # 1% fallback trailing offset
    ):
        self.symbol = symbol
        self.side = side.upper()
        self.entry_price = entry_price
        self.activation_pct = activation_pct
        self.atr_multiplier = atr_multiplier
        self.default_offset_pct = default_offset_pct

        self.is_active: bool = False
        self.highest_price: float = entry_price
        self.lowest_price: float = entry_price
        self.current_stop_price: Optional[float] = None

    def update(self, current_price: float, current_atr: Optional[float] = None) -> Dict[str, Any]:
        """
        Updates the trailing stop level based on current price and market ATR.
        Returns state dictionary indicating if stop is hit.
        """
        is_long = self.side in ["BUY", "LONG"]
        stop_hit = False

        # Calculate dynamic trailing distance
        if current_atr and current_atr > 0:
            trailing_distance = current_atr * self.atr_multiplier
        else:
            trailing_distance = current_price * self.default_offset_pct

        if is_long:
            if current_price > self.highest_price:
                self.highest_price = current_price

            # Check if profit activation reached
            profit_pct = (self.highest_price - self.entry_price) / self.entry_price
            if profit_pct >= self.activation_pct:
                self.is_active = True

            if self.is_active:
                new_stop = self.highest_price - trailing_distance
                if self.current_stop_price is None or new_stop > self.current_stop_price:
                    self.current_stop_price = new_stop

            # Check stop condition
            if self.current_stop_price is not None and current_price <= self.current_stop_price:
                stop_hit = True

        else:  # SHORT
            if current_price < self.lowest_price:
                self.lowest_price = current_price

            profit_pct = (self.entry_price - self.lowest_price) / self.entry_price
            if profit_pct >= self.activation_pct:
                self.is_active = True

            if self.is_active:
                new_stop = self.lowest_price + trailing_distance
                if self.current_stop_price is None or new_stop < self.current_stop_price:
                    self.current_stop_price = new_stop

            # Check stop condition
            if self.current_stop_price is not None and current_price >= self.current_stop_price:
                stop_hit = True

        return {
            "is_active": self.is_active,
            "stop_price": self.current_stop_price,
            "stop_hit": stop_hit,
            "current_price": current_price
        }
