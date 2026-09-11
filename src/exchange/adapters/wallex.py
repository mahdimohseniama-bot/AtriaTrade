import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from ..base_exchange import BaseExchangeAdapter
from ..models import Ticker, OrderResponse
from ..utils import retry_on_network_error
from ..validation import normalize_symbol, validate_order_inputs

load_dotenv()


class WallexAdapter(BaseExchangeAdapter):
    """آداپتور اتصال زنده به صرافی والکس (Wallex).
    
    این ماژول برای دریافت اطلاعات زنده و ارسال امن سفارشات طراحی شده است.
    """

    LIVE_ORDER_EXECUTION_ENABLED: bool = False

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.wallex.ir"
        self.api_key = api_key or os.getenv("WALLEX_API_KEY", "")
        self.session = requests.Session()
        
        if self.api_key and self.api_key != "your_wallex_api_key_here":
            self.session.headers.update({
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            })

    def format_symbol(self, symbol: str) -> str:
        """تبدیل نماد ورودی به فرمت استاندارد والکس (مانند BTCUSDT یا BTCTMN)."""
        normalized_symbol, base_asset, quote_asset = normalize_symbol(symbol)
        # در والکس معمولا IRT به TMN مپ می‌شود یا مستقیما پیوسته استفاده می‌شود
        if quote_asset == "IRT":
            return f"{base_asset}TMN"
        return f"{base_asset}{quote_asset}"

    @retry_on_network_error(max_retries=3)
    def test_connection(self) -> bool:
        """بررسی اتصال به سرور والکس از طریق اندپوینت مارکت‌ها."""
        url = f"{self.base_url}/v1/markets"
        response = self.session.get(url, timeout=5)
        return response.status_code == 200

    @retry_on_network_error(max_retries=3)
    def get_ticker(self, symbol: str) -> Ticker:
        """دریافت قیمت لحظه‌ای و وضعیت بازار نماد مورد نظر."""
        wallex_symbol = self.format_symbol(symbol)
        url = f"{self.base_url}/v1/markets"
        response = self.session.get(url, timeout=5)
        
        if response.status_code != 200:
            raise ConnectionError(f"Wallex API error: HTTP {response.status_code}")
            
        data = response.json()
        result = data.get("result", {})
        symbols_data = result.get("symbols", {})

        if wallex_symbol not in symbols_data:
            raise ValueError(f"Symbol '{wallex_symbol}' not found in Wallex markets.")

        market_info = symbols_data[wallex_symbol]
        stats = market_info.get("stats", {})

        bid_price = float(stats.get("bidPrice", 0.0) or 0.0)
        ask_price = float(stats.get("askPrice", 0.0) or 0.0)
        last_price = float(stats.get("lastPrice", 0.0) or 0.0)
        volume = float(stats.get("24h_volume", 0.0) or 0.0)

        normalized_symbol, _, _ = normalize_symbol(symbol)

        return Ticker(
            symbol=normalized_symbol,
            bid=bid_price,
            ask=ask_price,
            last_price=last_price,
            volume=volume
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
        """ارسال سفارش با اعتبارسنجی کامل و لایه‌های ایمنی kill-switch."""
        (
            norm_symbol,
            norm_side,
            norm_type,
            norm_qty,
            norm_price,
            base_asset,
            quote_asset
        ) = validate_order_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )

        if not self.api_key or self.api_key == "your_wallex_api_key_here":
            raise PermissionError("API key is not configured for Wallex.")

        if not self.LIVE_ORDER_EXECUTION_ENABLED:
            raise PermissionError(
                "Live order execution is disabled on WallexAdapter (LIVE_ORDER_EXECUTION_ENABLED is False). "
                "Use WallexPaperAdapter for simulation."
            )

        wallex_symbol = self.format_symbol(symbol)
        url = f"{self.base_url}/v1/order"
        payload: Dict[str, Any] = {
            "symbol": wallex_symbol,
            "type": norm_side.lower(),
            "order_type": norm_type.lower(),
            "quantity": str(norm_qty)
        }
        if norm_type == "LIMIT":
            payload["price"] = str(norm_price)

        response = self.session.post(url, json=payload, timeout=5)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Wallex order placement failed: {response.text}")

        res_data = response.json().get("result", {})
        order_id = str(res_data.get("clientOrderId", res_data.get("id", "live_wallex_order")))

        return OrderResponse(
            order_id=order_id,
            symbol=norm_symbol,
            status="FILLED" if norm_type == "MARKET" else "OPEN",
            price=norm_price if norm_price > 0 else 0.0,
            quantity=norm_qty,
            filled_quantity=norm_qty if norm_type == "MARKET" else 0.0,
            raw_data=res_data
        )
