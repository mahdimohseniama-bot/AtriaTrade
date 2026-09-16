import os
from typing import Optional

import requests
from dotenv import load_dotenv

from ...exchange.base_exchange import BaseExchangeAdapter
from ...exchange.models import OrderResponse, Ticker
from ...exchange.utils import retry_on_network_error
from ...exchange.validation import normalize_symbol, validate_order_inputs

load_dotenv()


class NobitexAdapter(BaseExchangeAdapter):
    """
    آداپتور نوبیتکس.

    وضعیت ایمنی فعلی پروژه:
    - دریافت داده بازار مجاز است.
    - ارسال سفارش واقعی مسدود است.
    - برای سفارش‌ها فقط از Dummy Exchange، Paper Trading یا Testnet استفاده شود.
    """

    LIVE_ORDER_EXECUTION_ENABLED = False

    def __init__(self, api_token: Optional[str] = None):
        self.base_url = "https://api.nobitex.ir"
        self.api_token = api_token or os.getenv("NOBITEX_API_TOKEN", "")
        self.session = requests.Session()

        if (
            self.api_token
            and self.api_token != "your_nobitex_token_here"
        ):
            self.session.headers.update(
                {"Authorization": f"Token {self.api_token}"}
            )

    @retry_on_network_error(max_retries=3)
    def test_connection(self) -> bool:
        response = self.session.get(
            f"{self.base_url}/market/stats",
            params={
                "srcCurrency": "btc",
                "dstCurrency": "usdt",
            },
            timeout=5,
        )
        return response.status_code == 200

    @retry_on_network_error(max_retries=3)
    def get_ticker(self, symbol: str) -> Ticker:
        normalized_symbol, base_asset, quote_asset = normalize_symbol(symbol)
        nobitex_symbol = f"{base_asset}-{quote_asset}".lower()

        response = self.session.get(
            f"{self.base_url}/market/stats",
            params={
                "srcCurrency": base_asset.lower(),
                "dstCurrency": quote_asset.lower(),
            },
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise ValueError(
                f"Nobitex API returned an error for "
                f"symbol {normalized_symbol}: {data}"
            )

        stats = data.get("stats", {}).get(nobitex_symbol, {})

        if not stats:
            raise ValueError(
                f"Symbol {normalized_symbol} was not found "
                f"in Nobitex market statistics."
            )

        return Ticker(
            symbol=normalized_symbol,
            bid=float(stats.get("bestBuy", 0.0)),
            ask=float(stats.get("bestSell", 0.0)),
            last_price=float(stats.get("latest", 0.0)),
            volume=float(stats.get("volumeSrc", 0.0)),
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
        """
        این متد عمداً از ارسال سفارش واقعی جلوگیری می‌کند.

        اعتبارسنجی ورودی ابتدا انجام می‌شود تا قرارداد استاندارد سفارش
        در همه Adapterها رعایت شود؛ سپس اجرای واقعی مسدود خواهد شد.
        """
        validate_order_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        if not self.api_token or self.api_token == "your_nobitex_token_here":
            raise PermissionError("API token is not configured for Nobitex.")

        if not self.LIVE_ORDER_EXECUTION_ENABLED:
            raise PermissionError(
                "Live order execution is disabled for Nobitex. "
                "Use DUMMY, Paper Trading, Backtesting, or Binance Testnet."
            )

        raise RuntimeError(
            "Live order execution must not be enabled in the current "
            "AtriaTrade safety mode."
        )
