import os
import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from ...exchange.base_exchange import BaseExchangeAdapter
from ...exchange.models import Ticker, OrderResponse
from ...exchange.utils import retry_on_network_error

load_dotenv()

class BinanceTestnetAdapter(BaseExchangeAdapter):
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.base_url = "https://testnet.binance.vision/api/v3"
        self.api_key = api_key or os.getenv("BINANCE_TESTNET_API_KEY", "")
        self.secret_key = secret_key or os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @retry_on_network_error(max_retries=3)
    def test_connection(self) -> bool:
        response = self.session.get(f"{self.base_url}/ping", timeout=5)
        return response.status_code == 200

    @retry_on_network_error(max_retries=3)
    def get_ticker(self, symbol: str) -> Ticker:
        price_resp = self.session.get(f"{self.base_url}/ticker/price", params={"symbol": symbol}, timeout=5)
        price_resp.raise_for_status()
        last_price = float(price_resp.json()["price"])

        book_resp = self.session.get(f"{self.base_url}/depth", params={"symbol": symbol, "limit": 5}, timeout=5)
        book_resp.raise_for_status()
        book_data = book_resp.json()
        
        best_bid = float(book_data["bids"][0][0]) if book_data.get("bids") else last_price
        best_ask = float(book_data["asks"][0][0]) if book_data.get("asks") else last_price

        return Ticker(
            symbol=symbol,
            bid=best_bid,
            ask=best_ask,
            last_price=last_price,
            volume=0.0
        )

    @retry_on_network_error(max_retries=3)
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> OrderResponse:
        if not self.api_key or not self.secret_key or self.api_key == "your_testnet_api_key_here":
            raise PermissionError("API keys are not configured for Binance Testnet.")

        endpoint = f"{self.base_url}/order"
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "timestamp": int(time.time() * 1000)
        }
        
        if order_type.upper() == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        params["signature"] = signature

        response = self.session.post(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return OrderResponse(
            order_id=str(data.get("orderId")),
            symbol=data.get("symbol"),
            status=data.get("status"),
            price=float(data.get("price") or 0.0),
            quantity=float(data.get("origQty")),
            filled_quantity=float(data.get("executedQty")),
            raw_data=data
        )
