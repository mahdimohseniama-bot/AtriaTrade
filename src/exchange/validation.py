import math
import re
from typing import Tuple


SUPPORTED_QUOTE_ASSETS = (
    "USDT",
    "USDC",
    "IRT",
    "BTC",
    "ETH",
)


def normalize_symbol(symbol: str) -> Tuple[str, str, str]:
    """
    تبدیل نمادهای رایج به ساختار استاندارد.

    نمونه‌ها:
    BTCUSDT  -> ("BTCUSDT", "BTC", "USDT")
    BTC-USDT -> ("BTCUSDT", "BTC", "USDT")
    BTC/USDT -> ("BTCUSDT", "BTC", "USDT")
    USDTIRT  -> ("USDTIRT", "USDT", "IRT")
    """
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string.")

    normalized = re.sub(r"[^A-Za-z0-9]", "", symbol).upper()

    if not normalized:
        raise ValueError("Symbol cannot be empty.")

    if not normalized.isalnum():
        raise ValueError(f"Invalid symbol format: {symbol}")

    for quote_asset in SUPPORTED_QUOTE_ASSETS:
        if normalized.endswith(quote_asset):
            base_asset = normalized[:-len(quote_asset)]

            if base_asset:
                return normalized, base_asset, quote_asset

    supported_quotes = ", ".join(SUPPORTED_QUOTE_ASSETS)
    raise ValueError(
        f"Unsupported symbol '{symbol}'. "
        f"Supported quote assets: {supported_quotes}"
    )


def normalize_side(side: str) -> str:
    """اعتبارسنجی و استانداردسازی سمت سفارش."""
    if not isinstance(side, str):
        raise ValueError("Order side must be a string.")

    normalized = side.strip().upper()

    if normalized not in {"BUY", "SELL"}:
        raise ValueError("Order side must be BUY or SELL.")

    return normalized


def normalize_order_type(order_type: str) -> str:
    """اعتبارسنجی و استانداردسازی نوع سفارش."""
    if not isinstance(order_type, str):
        raise ValueError("Order type must be a string.")

    normalized = order_type.strip().upper()

    if normalized not in {"MARKET", "LIMIT"}:
        raise ValueError("Order type must be MARKET or LIMIT.")

    return normalized


def validate_positive_number(value: float, field_name: str) -> float:
    """بررسی مثبت، عددی و متناهی بودن مقدار."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc

    if not math.isfinite(numeric_value):
        raise ValueError(f"{field_name} must be finite.")

    if numeric_value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return numeric_value


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = 0.0,
) -> Tuple[str, str, str, float, float, str, str]:
    """
    اعتبارسنجی کامل ورودی سفارش.

    خروجی:
    normalized_symbol, normalized_side, normalized_order_type,
    normalized_quantity, normalized_price, base_asset, quote_asset
    """
    normalized_symbol, base_asset, quote_asset = normalize_symbol(symbol)
    normalized_side = normalize_side(side)
    normalized_order_type = normalize_order_type(order_type)
    normalized_quantity = validate_positive_number(quantity, "Quantity")

    normalized_price = 0.0

    if normalized_order_type == "LIMIT":
        normalized_price = validate_positive_number(price, "Price")

    return (
        normalized_symbol,
        normalized_side,
        normalized_order_type,
        normalized_quantity,
        normalized_price,
        base_asset,
        quote_asset,
    )
