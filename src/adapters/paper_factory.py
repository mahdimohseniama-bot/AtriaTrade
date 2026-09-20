from typing import Dict, Optional, Any, Union
from src.adapters.nobitex_paper import NobitexPaperAdapter
from src.adapters.wallex_paper import WallexPaperAdapter


class PaperExchangeFactory:
    """Factory class to instantiate Paper Trading adapters flexibly."""

    SUPPORTED_EXCHANGES = ["nobitex", "wallex"]

    @classmethod
    def create_adapter(
        cls,
        exchange_name: str,
        initial_balances: Optional[Dict[str, float]] = None,
        initial_balance: Optional[Union[float, int]] = None,
        **kwargs: Any
    ):
        name = exchange_name.strip().lower()
        
        # اگر کاربر initial_balance تکی پاس داده بود، تبدیل به ساختار کیف پول والکس/نوبیتکس
        balances = initial_balances or {}
        if initial_balance is not None and not initial_balances:
            if name == "wallex":
                balances = {"tm": float(initial_balance), "usdt": 1000.0, "btc": 0.05}
            elif name == "nobitex":
                balances = {"rls": float(initial_balance), "usdt": 1000.0, "btc": 0.05}

        balances_to_pass = balances if balances else None

        if name == "nobitex":
            return NobitexPaperAdapter(initial_balances=balances_to_pass)
        elif name == "wallex":
            return WallexPaperAdapter(initial_balances=balances_to_pass)
        else:
            raise ValueError(
                f"Unsupported paper exchange '{exchange_name}'. Supported: {', '.join(cls.SUPPORTED_EXCHANGES)}"
            )


# Aliases for maximum compatibility
PaperFactory = PaperExchangeFactory
