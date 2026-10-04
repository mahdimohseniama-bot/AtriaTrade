import os
from typing import Dict, Any, Optional
from src.exchange.wallex_live_guard import WallexLiveGuard

class MockOrderBookFetcher:
    def fetch_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        return {"bid": 100000.0, "ask": 100100.0, "spread_pct": 0.1}

class WallexLiveRouter:
    def __init__(self, dry_run: bool = True, max_allowed_spread_pct: float = 0.5, fetcher: Any = None):
        self.dry_run = dry_run
        self.max_allowed_spread_pct = max_allowed_spread_pct
        self.fetcher = fetcher or MockOrderBookFetcher()
        self.guard = WallexLiveGuard()

    def process_strategy_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        symbol = signal.get("symbol", "TMNUSDT")
        price = float(signal.get("price", 0.0))
        quantity = float(signal.get("quantity", 0.0))
        action = signal.get("action", signal.get("side", "BUY")).upper()

        if not self.dry_run:
            if not self.guard.can_execute_safely():
                return {
                    "status": "BLOCKED",
                    "reason": "GUARD_PREFLIGHT_PREVENTED_EXECUTION"
                }

        ob = self.fetcher.fetch_orderbook(symbol) if hasattr(self.fetcher, "fetch_orderbook") else None
        if ob:
            spread_pct = ob.get("spread_pct")
            if spread_pct is None and "bid" in ob and "ask" in ob and ob["bid"] > 0:
                spread_pct = ((ob["ask"] - ob["bid"]) / ob["bid"]) * 100.0

            if spread_pct is not None and spread_pct > self.max_allowed_spread_pct:
                return {
                    "status": "REJECTED",
                    "reason": "SPREAD_EXCEEDS_THRESHOLD"
                }

        mode_str = "DRY_RUN" if self.dry_run else "LIVE"
        return {
            "status": "COMPLETED",
            "mode": mode_str,
            "executed_price": price,
            "quantity": quantity,
            "symbol": symbol,
            "side": action
        }
