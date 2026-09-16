import os
import requests
from typing import Optional
from src.exchange.base_exchange import BaseExchangeAdapter
from src.exchange.models import Ticker, OrderResponse


def validate_order_inputs(symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> None:
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Invalid symbol provided.")
    if side.upper() not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Expected 'BUY' or 'SELL'.")
    if order_type.upper() not in ["LIMIT", "MARKET"]:
        raise ValueError(f"Invalid order type: {order_type}. Expected 'LIMIT' or 'MARKET'.")
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if order_type.upper() == "LIMIT" and price <= 0:
        raise ValueError("Price must be greater than zero for LIMIT orders.")


class NobitexAdapter(BaseExchangeAdapter):
    """
    Nobitex Exchange Adapter (Spot)
    با لایه‌های سختگیرانه ایمنی برای جلوگیری از ثبت ناخواسته سفارشات واقعی.
    """
    LIVE_ORDER_EXECUTION_ENABLED = False

    def __init__(self, api_token: Optional[str] = None):
        self.base_url = "https://api.nobitex.ir"
        self.api_token = api_token if api_token is not None else os.getenv("NOBITEX_API_TOKEN", "")
        self.session = requests.Session()
        
        if self.api_token and self.api_token.strip() != "your_nobitex_token_here":
            self.session.headers.update({"Authorization": f"Token {self.api_token.strip()}"})

    def test_connection(self) -> bool:
        """بررسی اتصال به سرور نوبیتکس"""
        url = f"{self.base_url}/market/stats?srcCurrency=btc&dstCurrency=usdt"
        try:
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_ticker(self, symbol: str) -> Ticker:
        """
        دریافت قیمت زنده و اطلاعات جفت‌ارز از نوبیتکس
        """
        raw = symbol.upper().replace("-", "").replace("_", "")
        
        if raw.endswith("USDT"):
            src_curr = raw[:-4].lower()
            dst_curr = "usdt"
        elif raw.endswith("RLS"):
            src_curr = raw[:-3].lower()
            dst_curr = "rls"
        elif raw.endswith("IRT"):
            src_curr = raw[:-3].lower()
            dst_curr = "rls"
        else:
            src_curr = "btc"
            dst_curr = "usdt"

        url = f"{self.base_url}/market/stats?srcCurrency={src_curr}&dstCurrency={dst_curr}"
        resp = self.session.get(url, timeout=5)
        
        if resp.status_code != 200:
            raise ConnectionError(f"Nobitex API returned status code {resp.status_code}")
            
        data = resp.json()
        if data.get("status") != "ok":
            raise ValueError(f"Nobitex API error: {data}")

        stats_key = f"{src_curr}-{dst_curr}"
        stats = data.get("stats", {}).get(stats_key)
        if not stats:
            raise ValueError(f"Symbol stats not found for {symbol} (key: {stats_key})")

        return Ticker(
            symbol=raw,
            bid=float(stats.get("bestBuy", 0.0)),
            ask=float(stats.get("bestSell", 0.0)),
            last_price=float(stats.get("latest", 0.0)),
            volume=float(stats.get("volumeSrc", 0.0))
        )

    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: float = 0.0) -> OrderResponse:
        """
        ارسال سفارش به نوبیتکس همراه با قفل ایمنی.
        """
        validate_order_inputs(symbol=symbol, side=side, order_type=order_type, quantity=quantity, price=price)

        if not self.api_token or self.api_token.strip() == "":
            raise PermissionError("API token is not configured for Nobitex.")

        if not self.LIVE_ORDER_EXECUTION_ENABLED:
            raise PermissionError("Live order execution is disabled for Nobitex. Use DUMMY, Paper Trading, Backtesting, or Binance Testnet.")

        raise RuntimeError("Live order execution must not be enabled without explicit risk authorization.")
