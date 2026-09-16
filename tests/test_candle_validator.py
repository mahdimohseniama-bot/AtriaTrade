import math

import pytest

from src.data.candle_validator import CandleValidationError, CandleValidator


def make_candle(
    timestamp=1_720_000_000_000,
    open_price=100.0,
    high_price=110.0,
    low_price=95.0,
    close_price=105.0,
    volume=12.5,
):
    return {
        "timestamp": timestamp,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume,
    }


def test_validate_normalizes_dictionary_candles():
    validator = CandleValidator()

    result = validator.validate(
        [
            make_candle(timestamp=1_720_000_000),
            make_candle(timestamp=1_720_000_060),
        ],
        timeframe="1m",
        require_continuity=True,
    )

    assert len(result) == 2
    assert result[0]["timestamp"] == 1_720_000_000_000
    assert result[1]["timestamp"] == 1_720_000_060_000
    assert result[0]["open"] == 100.0
    assert result[0]["volume"] == 12.5


def test_validate_accepts_six_element_ohlcv_sequence():
    validator = CandleValidator()

    result = validator.validate(
        [
            [1_720_000_000_000, "100", "110", "95", "105", "2.75"],
        ]
    )

    assert result == [
        {
            "timestamp": 1_720_000_000_000,
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 2.75,
        }
    ]


@pytest.mark.parametrize(
    "field,value",
    [
        ("open", 0),
        ("high", -1),
        ("low", math.nan),
        ("close", math.inf),
        ("volume", -0.01),
    ],
)
def test_validate_rejects_invalid_numeric_values(field, value):
    validator = CandleValidator()
    candle = make_candle()
    candle[field] = value

    with pytest.raises(CandleValidationError):
        validator.validate([candle])


def test_validate_rejects_invalid_ohlc_relationship():
    validator = CandleValidator()

    invalid_candle = make_candle(
        open_price=100.0,
        high_price=99.0,
        low_price=95.0,
        close_price=98.0,
    )

    with pytest.raises(CandleValidationError, match="high"):
        validator.validate([invalid_candle])


def test_validate_rejects_duplicate_timestamps():
    validator = CandleValidator()

    candles = [
        make_candle(timestamp=1_720_000_000_000),
        make_candle(timestamp=1_720_000_000_000),
    ]

    with pytest.raises(CandleValidationError, match="تکراری"):
        validator.validate(candles)


def test_validate_rejects_descending_timestamps():
    validator = CandleValidator()

    candles = [
        make_candle(timestamp=1_720_000_060_000),
        make_candle(timestamp=1_720_000_000_000),
    ]

    with pytest.raises(CandleValidationError, match="باید از کندل قبلی بزرگ‌تر"):
        validator.validate(candles)


def test_validate_checks_candle_continuity_when_requested():
    validator = CandleValidator()

    candles = [
        make_candle(timestamp=1_720_000_000_000),
        make_candle(timestamp=1_720_000_120_000),
    ]

    with pytest.raises(CandleValidationError, match="فاصلهٔ زمانی"):
        validator.validate(
            candles,
            timeframe="1m",
            require_continuity=True,
        )


def test_validate_allows_time_gaps_when_continuity_is_disabled():
    validator = CandleValidator()

    candles = [
        make_candle(timestamp=1_720_000_000_000),
        make_candle(timestamp=1_720_000_120_000),
    ]

    result = validator.validate(
        candles,
        timeframe="1m",
        require_continuity=False,
    )

    assert len(result) == 2


def test_validate_rejects_empty_data_and_invalid_timeframe():
    validator = CandleValidator()

    with pytest.raises(CandleValidationError, match="خالی"):
        validator.validate([])

    with pytest.raises(CandleValidationError, match="timeframe نامعتبر"):
        validator.validate([make_candle()], timeframe="7m")


def test_validate_respects_maximum_candle_limit():
    validator = CandleValidator(max_candles=1)

    candles = [
        make_candle(timestamp=1_720_000_000_000),
        make_candle(timestamp=1_720_000_060_000),
    ]

    with pytest.raises(CandleValidationError, match="حد مجاز"):
        validator.validate(candles)
