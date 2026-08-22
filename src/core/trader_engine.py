import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from src.core.capital_manager import CapitalManager
from src.core.risk_manager import RiskManager, RiskConfig

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    status: str = "OPEN"
    pnl: float = 0.0

class TraderEngine:
    def __init__(self, capital_manager: Optional[CapitalManager] = None, risk_manager: Optional[RiskManager] = None):
        self.capital_mgr = capital_manager or CapitalManager(initial_capital=100.0)
        self.risk_mgr = risk_manager or RiskManager(RiskConfig())
        self.open_positions: List[Position] = []
        
    def open_virtual_position(self, symbol: str, side: str, current_price: float) -> Optional[Position]:
        status = self.capital_mgr.get_status()
        current_equity = status.get("current_capital", 0.0)
        
        # بررسی اجازه ریسک
        risk_decision = self.risk_mgr.can_trade(current_equity=current_equity)
        if hasattr(risk_decision, 'allowed') and not risk_decision.allowed:
            return None
            
        exits = self.risk_mgr.calculate_exit_levels(entry_price=current_price, side=side)
        stop_loss = exits.get("stop_loss_price")
        take_profit = exits.get("take_profit_price")
        
        size = self.risk_mgr.calculate_position_size(
            current_equity=current_equity,
            entry_price=current_price,
            stop_loss_price=stop_loss
        )
        
        if size <= 0:
            return None
            
        pos = Position(
            symbol=symbol,
            side=side,
            entry_price=current_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        self.open_positions.append(pos)
        return pos

    def close_virtual_position(self, symbol: str, exit_price: float) -> Optional[Position]:
        for pos in self.open_positions:
            if pos.symbol == symbol and pos.status == "OPEN":
                if pos.side.upper() == "BUY":
                    pnl = (exit_price - pos.entry_price) * pos.size
                else:
                    pnl = (pos.entry_price - exit_price) * pos.size
                
                pos.pnl = pnl
                pos.status = "CLOSED"
                
                self.capital_mgr.record_trade_result(net_pnl=pnl)
                self.risk_mgr.register_trade_result(pnl=pnl)
                
                self.open_positions.remove(pos)
                return pos
        return None

    def get_portfolio_summary(self) -> Dict[str, Any]:
        return {
            "capital_status": self.capital_mgr.get_status(),
            "open_positions": len(self.open_positions),
            "risk_status": self.risk_mgr.snapshot()
        }
