import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AtriaTrade.WallexBalanceSyncer")

class WallexBalanceSyncer:
    def __init__(self, client: Any):
        self.client = client
        self.cached_balances: Dict[str, float] = {}

    def fetch_balances(self) -> Dict[str, float]:
        """
        Fetches balances from Wallex client and parses them into asset: available mapping.
        """
        try:
            raw = self.client.get_balance()
            if not isinstance(raw, dict):
                logger.error("Invalid balance response format: expected dict")
                return self.cached_balances

            result = raw.get("result", {})
            balances_data = result.get("balances", {}) if isinstance(result, dict) else {}

            parsed: Dict[str, float] = {}
            for asset, details in balances_data.items():
                if isinstance(details, dict):
                    parsed[asset.upper()] = float(details.get("value", 0.0))
                elif isinstance(details, (int, float, str)):
                    parsed[asset.upper()] = float(details)

            self.cached_balances = parsed
            return self.cached_balances
        except Exception as e:
            logger.error(f"Failed to fetch Wallex balance: {str(e)}")
            return self.cached_balances

    def get_available(self, asset: str) -> float:
        """
        Returns available balance for a given asset (e.g. TMN, USDT, BTC).
        """
        return self.cached_balances.get(asset.upper(), 0.0)

    def has_sufficient_balance(self, asset: str, required_amount: float) -> bool:
        """
        Checks if available balance satisfies the required amount.
        """
        if required_amount <= 0:
            return False
        available = self.get_available(asset)
        return available >= required_amount
