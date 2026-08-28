"""Unified Paper Exchange Factory for AtriaTrade."""

from typing import Dict, Any, Optional
from src.adapters.nobitex_paper import NobitexPaperAdapter
from src.adapters.wallex_paper import WallexPaperAdapter


class PaperExchangeFactory:
    """Factory to create and retrieve simulated paper trading adapters."""

    SUPPORTED_EXCHANGES = ["nobitex", "wallex"]

    @classmethod
    def create_adapter(
        cls,
        exchange_name: str,
        initial_balances: Optional[Dict[str, float]] = None
    ) -> Any:
        """Create a paper trading adapter instance based on exchange name."""
        name = exchange_name.strip().lower()

        if name == "nobitex":
            return NobitexPaperAdapter(initial_balances=initial_balances)
        elif name == "wallex":
            return WallexPaperAdapter(initial_balances=initial_balances)
        else:
            raise ValueError(
                f"Unsupported paper exchange '{exchange_name}'. Supported: {', '.join(cls.SUPPORTED_EXCHANGES)}"
            )
