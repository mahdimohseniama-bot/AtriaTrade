from typing import Dict


class CapitalManager:
    """
    مدیریت سرمایه با تقسیم سود:
    ۶۰ درصد برای Vault
    ۴۰ درصد برای Compound
    """

    def __init__(
        self,
        initial_capital: float = 100.0,
        vault_ratio: float = 0.60,
        compound_ratio: float = 0.40,
        **kwargs,
    ):
        self.initial_capital = float(initial_capital)
        self.current_capital = float(initial_capital)

        self.vault_ratio = float(vault_ratio)
        self.compound_ratio = float(compound_ratio)

        if self.vault_ratio < 0 or self.compound_ratio < 0:
            raise ValueError("Profit ratios cannot be negative")

        if abs((self.vault_ratio + self.compound_ratio) - 1.0) > 1e-9:
            raise ValueError("vault_ratio + compound_ratio must equal 1.0")

        self.profit_reserve = 0.0

    @property
    def vault_balance(self) -> float:
        return self.profit_reserve

    @vault_balance.setter
    def vault_balance(self, value: float) -> None:
        self.profit_reserve = float(value)

    def record_trade_result(self, net_pnl: float) -> Dict[str, float]:
        return self.record_trade_pnl(net_pnl)

    def record_trade_pnl(self, net_pnl: float) -> Dict[str, float]:
        net_pnl = float(net_pnl)

        vault_share = 0.0
        compound_share = 0.0
        recovered_shortfall = 0.0

        if net_pnl < 0:
            self.current_capital += net_pnl

        elif net_pnl > 0:
            shortfall = max(
                0.0,
                self.initial_capital - self.current_capital,
            )

            recovered_shortfall = min(net_pnl, shortfall)
            self.current_capital += recovered_shortfall

            distributable_profit = net_pnl - recovered_shortfall

            if distributable_profit > 0:
                vault_share = distributable_profit * self.vault_ratio
                compound_share = distributable_profit * self.compound_ratio

                self.profit_reserve += vault_share
                self.current_capital += compound_share

        return {
            "net_pnl": net_pnl,
            "vault_share": vault_share,
            "compound_share": compound_share,
            "recovered_shortfall": recovered_shortfall,
            "current_capital": self.current_capital,
            "vault_balance": self.vault_balance,
            "profit_reserve": self.profit_reserve,
        }

    def get_status(self) -> Dict[str, float]:
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "profit_reserve": self.profit_reserve,
            "vault_balance": self.vault_balance,
            "total_value": self.current_capital + self.profit_reserve,
        }
