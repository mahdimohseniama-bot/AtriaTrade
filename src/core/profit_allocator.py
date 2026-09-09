"""
AtriaTrade - ProfitAllocator.

Single source of truth for the profit split model
"Reinvest + Cash Vault":

  * Reinvest: a configurable percentage of every NET realized profit
    is added back to the trading account cash so later trades
    compound on a bigger base.
  * Vault: the remaining percentage goes into vault_balance, a
    separate, liquid pool that is not reused for trading.

Input profit must be NET of fees (for example the realized_pnl value
returned by PortfolioManager.record_sell).
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ProfitSplitConfig:
    """Split settings. Ratios are percentages in the range [0, 100]."""

    reinvest_ratio: float = 70.0
    min_profit_to_split: float = 0.0

    def validate(self) -> None:
        if not (0.0 <= self.reinvest_ratio <= 100.0):
            raise ValueError("reinvest_ratio must be within [0, 100] percent")
        if self.min_profit_to_split < 0.0:
            raise ValueError("min_profit_to_split cannot be negative")


class ProfitAllocator:
    """Central profit split unit.

    One instance of this class should be the only authority deciding
    where every realized profit goes. It needs no monkeypatching and
    has no dependency on compatibility layers.

    Portfolio contract used by this class:
      - reinvest target: portfolio.cash must exist and be a float.
      - vault target: either vault_holder, or the portfolio itself,
        may expose vault_balance and optionally add_to_vault(amount).
    """

    def __init__(
        self,
        portfolio: Any = None,
        vault_holder: Any = None,
        reinvest_ratio: float = 70.0,
        min_profit_to_split: float = 0.0,
    ) -> None:
        self.config = ProfitSplitConfig(
            reinvest_ratio=reinvest_ratio,
            min_profit_to_split=min_profit_to_split,
        )
        self.config.validate()
        self.portfolio = portfolio
        self.vault_holder = vault_holder

        # Cumulative stats, useful for reporting and tests.
        self.total_profit: float = 0.0
        self.total_reinvested: float = 0.0
        self.total_vaulted: float = 0.0
        self.split_count: int = 0
        self.history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Small internal helpers
    # ------------------------------------------------------------------
    def _vault_target(self) -> Any:
        if self.vault_holder is not None:
            return self.vault_holder
        return self.portfolio

    def _get_vault_balance(self) -> float:
        holder = self._vault_target()
        if holder is None:
            return 0.0
        return float(getattr(holder, "vault_balance", 0.0) or 0.0)

    def _add_to_vault(self, amount: float) -> None:
        holder = self._vault_target()
        if holder is None or amount <= 0.0:
            return
        add = getattr(holder, "add_to_vault", None)
        if callable(add):
            add(amount)
        else:
            holder.vault_balance = self._get_vault_balance() + amount

    def _reinvest(self, amount: float) -> None:
        if self.portfolio is None or amount <= 0.0:
            return
        current = float(getattr(self.portfolio, "cash", 0.0) or 0.0)
        self.portfolio.cash = current + amount

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def split(self, net_profit: float) -> Dict[str, Any]:
        """Return the calculated split WITHOUT applying it.

        Useful for previews and math-only tests.
        """
        profit = float(net_profit)
        skipped = profit <= 0.0 or profit < self.config.min_profit_to_split
        if skipped:
            return {
                "profit": profit,
                "reinvest_amount": 0.0,
                "vault_amount": 0.0,
                "skipped": True,
            }
        reinvest = round(profit * self.config.reinvest_ratio / 100.0, 8)
        vault = round(profit - reinvest, 8)
        return {
            "profit": profit,
            "reinvest_amount": reinvest,
            "vault_amount": vault,
            "skipped": False,
        }

    def process_trade_profit(self, net_profit: float) -> Dict[str, Any]:
        """Main engine entry point.

        Takes a trade NET profit, splits it, applies it
        (reinvest -> portfolio.cash, remainder -> vault) and returns
        a summary dict describing what happened.
        """
        result = self.split(net_profit)
        self.history.append(dict(result))
        if result["skipped"]:
            return result

        self._reinvest(result["reinvest_amount"])
        self._add_to_vault(result["vault_amount"])

        self.total_profit += result["profit"]
        self.total_reinvested += result["reinvest_amount"]
        self.total_vaulted += result["vault_amount"]
        self.split_count += 1
        result["action"] = "split"
        result["split_count"] = self.split_count
        return result

    def get_summary(self) -> Dict[str, Any]:
        return {
            "reinvest_ratio": self.config.reinvest_ratio,
            "total_profit": round(self.total_profit, 8),
            "total_reinvested": round(self.total_reinvested, 8),
            "total_vaulted": round(self.total_vaulted, 8),
            "vault_balance": round(self._get_vault_balance(), 8),
            "split_count": self.split_count,
        }
