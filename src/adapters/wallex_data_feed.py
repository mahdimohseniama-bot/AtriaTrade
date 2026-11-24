import time
import requests
from typing import Dict, Any, Optional

class WallexDataFeed:
    """Live public market data feed for Wallex exchange without requiring private API keys."""
    
    BASE_URL = "https://api.wallex.ir"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AtriaTrade/1.0 (Termux; Android)"
        })

    def get_orderbook(self, symbol: str = "USDTTMN") -> Dict[str, Any]:
        """Fetch market depth/orderbook for a given pair."""
        url = f"{self.BASE_URL}/v1/depth"
        params = {"symbol": symbol}
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") or "result" in data:
                return {"status": "success", "data": data.get("result", data)}
            return {"status": "error", "message": "Unexpected response format", "raw": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_ticker_price(self, symbol: str = "USDTTMN") -> Optional[float]:
        """Fetch latest price for symbol."""
        depth = self.get_orderbook(symbol=symbol)
        if depth.get("status") == "success":
            result = depth.get("data", {})
            # Wallex depth format: result['ask'][0]['price'] / result['bid'][0]['price']
            asks = result.get("ask", [])
            bids = result.get("bid", [])
            if asks and bids:
                best_ask = float(asks[0]["price"])
                best_bid = float(bids[0]["price"])
                return round((best_ask + best_bid) / 2.0, 2)
        return None
