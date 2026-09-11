import os
import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from ..base_exchange import BaseExchangeAdapter
from ..models import Ticker, OrderResponse
from ..utils import retry_on_network_error
from ..validation import normalize_symbol, validate_order_inputs

load_dotenv()


class BinanceTestnetAdapter(BaseExchangeAdapter):
    """آداپتور بایننس تست‌نت با پشتیبانی کامل از استاندارد BaseExchangeAdapter."""

    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.base_url = "https://testnet.binance.vision/api/v3"
        self.api_key = api_key or os.getenv("BINANCE_TESTNET_API_KEY", "")
        self.secret_key = secret_key or os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
        self.session = requests.Session()
        if self.api_key and self.api_key != "your_testnet_api_key_here":
            self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def format_symbol(self, symbol: str) -> str:
        """تبدیل استاندارد نماد به فرمت بایننس (مثلاً BTCUSDT)."""
        normalized, base, quote = normalize_symbol(symbol)
        return f"{base}{quote}"

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @retry_on_network_error(max_retries=3)
    def test_connection(self) -> bool:
        url = f"{self.base_url}/ping"
        resp = self.session.get(url, timeout=5)
        return resp.status_code == 200

    @retry_on_network_error(max_retries=3)
    def get_ticker(self, symbol: str) -> Ticker:
        binance_symbol = self.format_symbol(symbol)
        url_price = f"{self.base_url}/ticker/price"
        resp_price = self.session.get(url_price, params={"symbol": binance_symbol}, timeout=5)
        if resp_price.status_code != 200:
            raise ConnectionError(f"Binance price error: HTTP {resp_price.status_code}")
        last_price = float(resp_price.json().get("price", 0.0))

        url_depth = f"{self.base_url}/depth"
        resp_depth = self.session.get(url_depth, params={"symbol": binance_symbol, "limit": 5}, timeout=5)
        best_bid, best_ask = last_price, last_price
        if resp_depth.status_code == 200:
            depth_data = resp_depth.json()
            bids = depth_data.get("bids", [])
            asks = depth_data.get("asks", [])
            if bids:
                best_bid = float(bids[0][0])
            if asks:
                best_ask = float(asks[0][0])

        return Ticker(
            symbol=binance_symbol,
            bid=best_bid,
            ask=best_ask,
            last_price=last_price,
            volume=0.0
        )

    @retry_on_network_error(max_retries=3)
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0
    ) -> OrderResponse:
        (
            norm_symbol,
            norm_side,
            norm_type,
            norm_qty,
            norm_price,
            _,
            _
        ) = validate_order_inputs(symbol, side, order_type, quantity, price)

        if not self.api_key or not self.secret_key or self.api_key == "your_testnet_api_key_here":
            raise PermissionError("API keys are not configured for Binance Testnet.")

        binance_symbol = self.format_symbol(norm_symbol)
        params: Dict[str, Any] = {
            "symbol": binance_symbol,
            "side": norm_side,
            "type": norm_type,
            "quantity": norm_qty,
            "timestamp": int(time.time() * 1000)
        }
        if norm_type == "LIMIT":
            params["price"] = norm_price
            params["timeInForce"] = "GTC"

        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        url = f"{self.base_url}/order?{query_string}&signature={signature}"

        resp = self.session.post(url, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Binance order error: {resp.text}")

        data = resp.json()
        return OrderResponse(
            order_id=str(data.get("orderId")),
            symbol=binance_symbol,
            status=data.get("status", "NEW"),
            price=float(data.get("price", 0.0)),
            quantity=float(data.get("origQty", 0.0)),
            filled_quantity=float(data.get("executedQty", 0.0)),
            raw_data=data
        )
