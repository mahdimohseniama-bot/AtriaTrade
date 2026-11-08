import requests
from typing import Optional, Dict, Any
from src.exchange.base_exchange import BaseExchangeAdapter
from src.exchange.models import Ticker, OrderResponse

class WallexAdapter(BaseExchangeAdapter):
    LIVE_ORDER_EXECUTION_ENABLED = False

    def __init__(self, api_token: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_token = api_token
        self.base_url = "https://api.wallex.ir/v1"
        self.headers = {"X-API-KEY": self.api_token} if self.api_token else {}

    def _get_headers(self) -> Dict[str, str]:
        return self.headers

    def test_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/markets", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_ticker(self, symbol: str) -> Ticker:
        try:
            response = requests.get(f"{self.base_url}/markets", headers=self.headers, timeout=10)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch ticker from Wallex: {response.text}")
            data = response.json()
            symbols_data = data.get("result", {}).get("symbols", {})
            if symbol not in symbols_data:
                raise ValueError(f"Symbol {symbol} not found on Wallex")
            stats = symbols_data[symbol].get("stats", {})
            return Ticker(
                symbol=symbol,
                bid=float(stats.get("bidPrice", 0.0)),
                ask=float(stats.get("askPrice", 0.0)),
                last_price=float(stats.get("lastPrice", 0.0)),
                volume=float(stats.get("24h_volume", 0.0))
            )
        except requests.RequestException as e:
            raise ConnectionError(f"Network error while fetching ticker: {str(e)}")

    def get_order_book(self, symbol: str) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/depth",
                headers=self.headers,
                params={"symbol": symbol},
                timeout=10
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch order book: {response.text}")
            data = response.json()
            return data.get("result", {})
        except requests.RequestException as e:
            raise ConnectionError(f"Network error while fetching order book: {str(e)}")

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> OrderResponse:
        if not self.api_token:
            raise PermissionError("API token is not configured for Wallex.")
        if not self.LIVE_ORDER_EXECUTION_ENABLED:
            raise PermissionError("Live order execution is disabled for Wallex. Use paper trading mode.")
        raise NotImplementedError("Wallex live trading is not enabled yet.")
