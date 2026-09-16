import pytest

from src.exchange.validation import (
    normalize_order_type,
    normalize_side,
    normalize_symbol,
    validate_order_inputs,
    validate_positive_number,
)


def test_normalize_symbol_accepts_common_formats():
    assert normalize_symbol("BTCUSDT") == ("BTCUSDT", "BTC", "USDT")
    assert normalize_symbol("btc-usdt") == ("BTCUSDT", "BTC", "USDT")
    assert normalize_symbol("BTC/USDT") == ("BTCUSDT", "BTC", "USDT")
    assert normalize_symbol("usdtirt") == ("USDTIRT", "USDT", "IRT")


def test_normalize_symbol_rejects_invalid_symbol():
    with pytest.raises(ValueError, match="Unsupported symbol"):
        normalize_symbol("BTCXYZ")

    with pytest.raises(ValueError, match="cannot be empty"):
        normalize_symbol("")


def test_order_side_and_type_validation():
    assert normalize_side("buy") == "BUY"
    assert normalize_side(" SELL ") == "SELL"
    assert normalize_order_type("market") == "MARKET"
    assert normalize_order_type(" LIMIT ") == "LIMIT"

    with pytest.raises(ValueError, match="BUY or SELL"):
        normalize_side("HOLD")

    with pytest.raises(ValueError, match="MARKET or LIMIT"):
        normalize_order_type("STOP")


def test_positive_number_validation():
    assert validate_positive_number("0.01", "Quantity") == 0.01

    with pytest.raises(ValueError, match="greater than zero"):
        validate_positive_number(0, "Quantity")

    with pytest.raises(ValueError, match="greater than zero"):
        validate_positive_number(-1, "Quantity")

    with pytest.raises(ValueError, match="must be finite"):
        validate_positive_number(float("inf"), "Quantity")


def test_validate_limit_order_inputs():
    result = validate_order_inputs(
        symbol="btc-usdt",
        side="buy",
        order_type="limit",
        quantity=0.01,
        price=60000.0,
    )

    assert result == (
        "BTCUSDT",
        "BUY",
        "LIMIT",
        0.01,
        60000.0,
        "BTC",
        "USDT",
    )


def test_limit_order_requires_positive_price():
    with pytest.raises(ValueError, match="Price must be greater than zero"):
        validate_order_inputs(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
            price=0,
        )
