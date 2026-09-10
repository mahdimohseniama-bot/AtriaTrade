import os
from typing import Optional

import requests

from src.exchange.base_exchange import BaseExchangeAdapter
from src.exchange.validation import normalize_symbol
from src.exchange.models import Ticker, OrderResponse
from src.exchange.utils import retry_on_network_error


class NobitexAdapter(BaseExchangeAdapter):
    LIVE_ORDER_EXECUTION_ENABLED = False

    def __init__(self, api_token: Optional[str] = None, **kwargs):
        # نام        آداپتور مطابق انتظار Runner و تست‌ها
        self.name = "nobitex"

        self.base_url = "https://api.nobitex.ir"

        # تفاوت مهم:
        # None یعنی پارامتر ارسال نشده و باید از محیط خوانده شود.
        # "" یعنی عمداً توکن خالی ارسال شده و نباید با مقدار محیطی جایگزین شود.
        if api_token is None:
            self.api_token = os.getenv("NOBITEX_API_TOKEN", "")
        else:
            self.api_token = api_token

        self.session = requests.Session()

        if self.api_token and self.api_token != "your_nobitex_token_here":
            self.session.headers.update({
                "Authorization": f"Token {self.api_token}"
            })

    def format_symbol(self, symbol: str) -> str:
        _, base, quote = normalize_symbol(symbol)
        return f"{base}-{quote}".lower()

    @retry_on_network_error(max_retries=3)
    def test_connection(self) -> bool:
        response = self.session.get(
            f"{self.base_url}/market/stats"
            "?srcCurrency=btc&dstCurrency=usdt",
            timeout=5
        )
        return response.status_code == 200

    @retry_on_network_error(max_retries=3)
    def get_ticker(self, symbol: str) -> Ticker:
        normalized, base, quote = normalize_symbol(symbol)
        nobitex_symbol = self.format_symbol(symbol)

        response = self.session.get(
            f"{self.base_url}/market/stats"
            f"?srcCurrency={base.lower()}"
            f"&dstCurrency={quote.lower()}",
            timeout=5
        )
        response.raise_for_status()

        data = response.json()
        stats = data.get("stats", {}).get(nobitex_symbol, {})

        return Ticker(
            symbol=normalized,
            bid=float(stats.get("bestBuy", 0)),
            ask=float(stats.get("bestSell", 0)),
            last_price=float(stats.get("latest", 0)),
            volume=float(stats.get("volumeSrc", 0)),
        )

    @retry_on_network_error(max_retries=3)
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0,
    ) -> OrderResponse:
        # این شرط باید قبل از LIVE_ORDER_EXECUTION_ENABLED بررسی شود
        # تا تست بدون توکن پیام صحیح را دریافت کند.
        if not self.api_token:
            raise PermissionError("API token is not configured")

        if not self.LIVE_ORDER_EXECUTION_ENABLED:
            raise PermissionError(
                "Live order execution is disabled for Nobitex. "
                "Use DUMMY, Paper Trading, Backtesting, or Binance Testnet."
            )

        raise RuntimeError(
            "Live order execution must not be enabled in the current "
            "AtriaTrade safety mode."
        )
