from datetime import timezone

import pytest

from src.core.historical_data_validator import (
    HistoricalDataValidationError,
    HistoricalDataValidator,
)


def make_candle(
    timestamp="2026-01-01T00:00:00Z",
    **overrides,
):
    data = {
        "timestamp": timestamp,
        "open": 100,
        "high": 110,
        "low": 90,
        "close": 105,
        "volume": 10,
    }
    data.update(overrides)
    return data


def test_valid_ohlcv_is_accepted_and_normalized():
    report = HistoricalDataValidator().validate(
        [make_candle()]
    )

    assert report.is_valid
    assert report.valid_rows == 1
    assert report.invalid_rows == 0
    assert report.normalized_rows[0]["close"] == 105.0
    assert report.normalized_rows[0]["timestamp"].tzinfo == timezone.utc


def test_required_fields_are_checked():
    data = make_candle()
    del data["volume"]

    report = HistoricalDataValidator().validate([data])

    assert not report.is_valid
    assert any(
        issue.code == "missing_field"
        for issue in report.issues
    )


@pytest.mark.parametrize(
    "field,value,expected_code",
    [
        ("open", 0, "non_positive_price"),
        ("close", -1, "non_positive_price"),
        ("volume", 0, "non_positive_volume"),
        ("volume", -5, "non_positive_volume"),
    ],
)
def test_invalid_positive_values_are_rejected(
    field,
    value,
    expected_code,
):
    report = HistoricalDataValidator().validate(
        [make_candle(**{field: value})]
    )

    assert not report.is_valid
    assert any        for issue in report expected_code
        for issue in report.issues
    )


def test_high_and_low_relationships_are_checked():
    report = HistoricalDataValidator().validate(
        [make_candle(high=101, low=99)]
    )

    codes = {issue.code for issue in report.issues}

    assert not report.is_valid
    assert "invalid_high" in codes
    assert "invalid_low" in codes


def test_nan_and_infinity_are_rejected():
    report = HistoricalDataValidator().validate(
        [
            make_candle(close=float("nan")),
            make_candle(
                timestamp="2026-01-01T00:01:00Z",
                volume=float("inf"),
            ),
        ]
    )

    assert not report.is_valid
    assert sum(
        issue.code == "non_finite"
        for issue in report.issues
    ) == 2


def test_duplicate_timestamps_are_detected():
    report = HistoricalDataValidator().validate(
        [
            make_candle(),
            make_candle(close=106),
        ]
    )

    assert not report.is_valid
    assert len(report.duplicate_timestamps) == 1
    assert any(
        issue.code == "duplicate_timestamp"
        for issue in report.issues
    )


def test_out_of_order_timestamps_are_detected():
    report = HistoricalDataValidator().validate(
        [
            make_candle("2026-01-01T00:01:00Z"),
            make_candle("2026-01-01T00:00:00Z"),
        ]
    )

    assert not report.is_valid
    assert any(
        issue.code == "out_of_order"
        for issue in report.issues
    )


def test_time_gaps_are_reported_as_warnings():
    report = HistoricalDataValidator(
        interval_seconds=60,
    ).validate(
        [
            make_candle("2026-01-01T00:00:00Z"),
            make_candle("2026-01-01T00:03:00Z"),
        ]
    )

    assert report.is_valid
    assert len(report.gaps) == 1
    assert report.warning_count == 1
    assert report.gaps[0][2] == 180


def test_alias_columns_are_supported():
    report = HistoricalDataValidator().validate(
        [
            {
                "time": 1767225600,
                "o": "100",
                "h": "110",
                "l": "90",
                "c": "105",
                "v": "10",
            }
        ]
    )

    assert report.is_valid
    assert report.normalized_rows[0]["open"] == 100.0


def test_empty_dataset_is_invalid():
    report = HistoricalDataValidator().validate([])

    assert not report.is_valid
    assert report.issues[0].code == "empty_dataset"


def test_strict_mode_raises_for_invalid_data():
    with pytest.raises(HistoricalDataValidationError):
        HistoricalDataValidator().validate(
            [make_candle(volume=0)],
            raise_on_error=True,
        )


def test_report_can_be_serialized_to_dict():
    report = HistoricalDataValidator().validate(
        [make_candle()]
    )

    result = report.as_dict()

    assert result["is_valid"] is True
    assert result["total_rows"] == 1
    assert result["valid_rows"] == 1
    assert isinstance(result["issues"], list)
