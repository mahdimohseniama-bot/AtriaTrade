"""
Break-Even and Multi-Target Take Profit Orchestrator for AtriaTrade (Capability 76).
Automates trade risk elimination (Break-Even) and partial profit realization (TP1, TP2, TP3).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TakeProfitTarget:
    target_id: int
    price: float
    percentage_to_close: float  # e.g., 0.50 for 50%
    is_hit: bool = False


@dataclass
class ManagedTrade:
    trade_id: str
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    current_size: float
    stop_loss: float
    take_profits: List[TakeProfitTarget] = field(default_factory=list)
    is_breakeven: bool = False
    fee_buffer_percent: float = 0.001  # 0.1% buffer for exchange fees
    realized_pnl: float = 0.0


class BreakEvenTPOrchestrator:
    def __init__(self, auto_be_on_tp1: bool = True):
        self.auto_be_on_tp1 = auto_be_on_tp1

    def evaluate_price_update(
        self,
        trade: ManagedTrade,
        current_high: float,
        current_low: float
    ) -> Dict[str, Any]:
        """
        Evaluates current bar/tick prices against TP targets and updates stop-loss to break-even.
        """
        events: List[str] = []
        is_buy = trade.direction.upper() == "BUY"

        for tp in trade.take_profits:
            if tp.is_hit:
                continue

            hit = False
            if is_buy and current_high >= tp.price:
                hit = True
            elif not is_buy and current_low <= tp.price:
                hit = True

            if hit:
                tp.is_hit = True
                close_size = round(trade.current_size * tp.percentage_to_close, 6)
                trade.current_size = round(trade.current_size - close_size, 6)
                
                # Calculate realized profit on closed portion
                if is_buy:
                    pnl = (tp.price - trade.entry_price) * close_size
                else:
                    pnl = (trade.entry_price - tp.price) * close_size
                
                trade.realized_pnl += round(pnl, 4)
                events.append(f"TP{tp.target_id}_HIT")

                # If TP1 is hit and auto-BE is enabled, move SL to Break-Even
                if tp.target_id == 1 and self.auto_be_on_tp1 and not trade.is_breakeven:
                    self.move_to_breakeven(trade)
                    events.append("MOVED_TO_BREAKEVEN")

        return {
            "trade_id": trade.trade_id,
            "events": events,
            "remaining_size": trade.current_size,
            "stop_loss": trade.stop_loss,
            "is_breakeven": trade.is_breakeven,
            "realized_pnl": trade.realized_pnl
        }

    def move_to_breakeven(self, trade: ManagedTrade) -> None:
        """
        Moves the stop-loss to entry price +/- fee buffer.
        """
        if trade.direction.upper() == "BUY":
            new_sl = trade.entry_price * (1.0 + trade.fee_buffer_percent)
            if new_sl > trade.stop_loss:
                trade.stop_loss = round(new_sl, 4)
                trade.is_breakeven = True
        else:
            new_sl = trade.entry_price * (1.0 - trade.fee_buffer_percent)
            if new_sl < trade.stop_loss:
                trade.stop_loss = round(new_sl, 4)
                trade.is_breakeven = True
