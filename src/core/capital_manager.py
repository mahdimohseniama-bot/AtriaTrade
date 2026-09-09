"""
Capital & Profit Management Module for AtriaTrade.
Handles:
- Working capital tracking
- Vault (Profit Reserve) accumulation
- Drawdown recovery mechanism
- 60/40 Profit split (60% Working Capital Compound / 40% Vault)
"""
from typing import Dict, Any

class CapitalManager:
    def __init__(self, initial_capital: float = 100.0, compound_ratio: float = 0.60):
        self.initial_capital = float(initial_capital)
        self.current_capital = float(initial_capital)
        self.profit_reserve = 0.0
        self.compound_ratio = float(compound_ratio)  # 60% compound, 40% vault

    def record_trade_result(self, net_pnl: float = 0.0, **kwargs) -> Dict[str, float]:
        """
        Record trade result supporting both net_pnl and profit keyword arguments.
        """
        if "profit" in kwargs:
            net_pnl = kwargs["profit"]
        
        net_pnl = float(net_pnl)

        if net_pnl > 0:
            shortfall = max(0.0, self.initial_capital - self.current_capital)
            if shortfall > 0:
                recovery = min(shortfall, net_pnl)
                self.current_capital += recovery
                remaining_profit = net_pnl - recovery
            else:
                remaining_profit = net_pnl

            if remaining_profit > 0:
                to_compound = remaining_profit * self.compound_ratio
                to_vault = remaining_profit * (1.0 - self.compound_ratio)
                self.current_capital += to_compound
                self.profit_reserve += to_vault
        elif net_pnl < 0:
            self.current_capital -= abs(net_pnl)

        return self.get_status()

    def get_working_capital(self) -> float:
        return round(self.current_capital, 4)

    def get_vault_balance(self) -> float:
        return round(self.profit_reserve, 4)

    def get_total_capital(self) -> float:
        return round(self.current_capital + self.profit_reserve, 4)

    def get_current_capital(self) -> float:
        return self.get_working_capital()

    def get_status(self) -> Dict[str, float]:
        return {
            "initial_capital": round(self.initial_capital, 4),
            "working_capital": self.get_working_capital(),
            "vault_balance": self.get_vault_balance(),
            "total_capital": self.get_total_capital(),
            "current_capital": self.get_working_capital(),
            "profit_reserve": self.get_vault_balance(),
            "total_value": self.get_total_capital()
        }
