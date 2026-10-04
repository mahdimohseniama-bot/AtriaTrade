import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class PreflightResult:
    status: str
    reasons: List[str] = field(default_factory=list)

class WallexPreflightFetcher:
    def fetch_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        return {"spread_pct": 0.2, "bid": 60000.0, "ask": 60120.0}

class WallexPreflight:
    def __init__(self, symbol: str = "TMNUSDT", api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.symbol = symbol
        self.api_key = api_key or os.environ.get("WALLEX_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("WALLEX_API_SECRET", "")
        self.orderbook = WallexPreflightFetcher()

    def _get_account_balances(self) -> Optional[Dict[str, float]]:
        if not self.api_key or not self.api_secret:
            return None
        return {"TMN": 1000000.0, "USDT": 50.0}

    def run(self) -> PreflightResult:
        reasons = []

        if os.environ.get("ALLOW_WALLEX_LIVE", "0") != "1":
            reasons.append("ALLOW_WALLEX_LIVE_DISABLED")

        if os.environ.get("WALLEX_KILL_SWITCH", "0") == "1":
            reasons.append("KILL_SWITCH_ACTIVE")

        ob = self.orderbook.fetch_orderbook(self.symbol)
        if ob is None:
            reasons.append("ORDERBOOK_UNAVAILABLE")

        bal = self._get_account_balances()
        if bal is None:
            reasons.append("ACCOUNT_UNAVAILABLE")

        if reasons:
            return PreflightResult(status="NOT_READY", reasons=reasons)
        return PreflightResult(status="READY", reasons=[])
