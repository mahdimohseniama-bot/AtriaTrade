import pytest
from datetime import datetime, timezone, timedelta
from src.core.historical_data_validator import (
    HistoricalDataValidator,
    ValidationIssue,
    ValidationReport,
)

def make_candle(
    timestamp="2026-01-01T00:00:00Z",
    open=100.0,
    high=105.0,
    low=95.0,
    close=102.0,
    volume=10.0,
    **kwargs
):
    candle = {
        "timestamp": timestamp,
        "open": open,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }
    candle.update(kwargs)
    return candle

def test_empty_dataset_returns_error():
    report = HistoricalDataValidator().validate([])
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "EMPTY_DATASET" in codes

def test_valid_dataset_passes():
    candles = [
        make_candle(timestamp="2026-01-01T00:00:00Z", open=100, high=105, low=95, close=102, volume=10),
        make_candle(timestamp="2026-01-01T00:01:00Z", open=102, high=106, low=101, close=104, volume=15),
    ]
    report = HistoricalDataValidator(timeframe_minutes=1).validate(candles)
    assert report.is_valid
    assert len(report.issues) == 0

@pytest.mark.parametrize(
    "field,value,expected_code",
    [
        ("open", -1.0, "INVALID_PRICE"),
        ("high", -5.0, "INVALID_PRICE"),
        ("low", 0.0, "INVALID_PRICE"),
        ("close", -2.0, "INVALID_PRICE"),
        ("volume", -10.0, "INVALID_VOLUME"),
        ("open", "invalid", "INVALID_PRICE_TYPE"),
        ("volume", None, "INVALID_VOLUME_TYPE"),
    ],
)
def test_price_and_volume_value_validation(field, value, expected_code):
    report = HistoricalDataValidator().validate([make_candle(**{field: value})])
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert expected_code in codes

def test_high_and_low_relationships_are_checked():
    report = HistoricalDataValidator().validate([make_candle(high=101, low=99, open=102, close=100)])
    codes = {issue.code for issue in report.issues}
    assert not report.is_valid
    assert "HIGH_LESS_THAN_OPEN_OR_CLOSE" in codes

def test_low_greater_than_open_or_close_checked():
    report = HistoricalDataValidator().validate([make_candle(high=110, low=101, open=100, close=105)])
    codes = {issue.code for issue in report.issues}
    assert not report.is_valid
    assert "LOW_GREATER_THAN_OPEN_OR_CLOSE" in codes

def test_missing_required_fields_reported():
    candle = make_candle()
    del candle["close"]
    report = HistoricalDataValidator().validate([candle])
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "MISSING_FIELD" in codes

def test_timestamp_parsing_and_order():
    candles = [
        make_candle(timestamp="2026-01-01T00:05:00Z"),
        make_candle(timestamp="2026-01-01T00:01:00Z"),
    ]
    report = HistoricalDataValidator().validate(candles)
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "UNSORTED_TIMESTAMPS" in codes

def test_duplicate_timestamps_detected():
    candles = [
        make_candle(timestamp="2026-01-01T00:00:00Z"),
        make_candle(timestamp="2026-01-01T00:00:00Z"),
    ]
    report = HistoricalDataValidator().validate(candles)
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "DUPLICATE_TIMESTAMP" in codes

def test_timeframe_gap_detection():
    candles = [
        make_candle(timestamp="2026-01-01T00:00:00Z"),
        make_candle(timestamp="2026-01-01T00:05:00Z"),
    ]
    report = HistoricalDataValidator(timeframe_minutes=1).validate(candles)
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "MISSING_CANDLE_GAP" in codes

def test_invalid_timestamp_format():
    candles = [make_candle(timestamp="not-a-date")]
    report = HistoricalDataValidator().validate(candles)
    assert not report.is_valid
    codes = {issue.code for issue in report.issues}
    assert "INVALID_TIMESTAMP_FORMAT" in codes

def test_summary_and_error_count():
    candles = [
        make_candle(timestamp="2026-01-01T00:00:00Z", open=-10),
        make_candle(timestamp="2026-01-01T00:01:00Z", volume=-5),
    ]
    report = HistoricalDataValidator().validate(candles)
    assert not report.is_valid
    assert report.error_count >= 2
    assert isinstance(report.to_dict(), dict)
