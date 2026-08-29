"""Unit tests for VolumeProfileEngine (Capability 102)."""

import pytest
from src.core.volume_profile_engine import VolumeProfileEngine


@pytest.fixture
def engine():
    return VolumeProfileEngine(num_bins=20, value_area_pct=0.70)


def test_calculate_profile_insufficient_data(engine):
    res = engine.calculate_profile([])
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["poc_price"] == 0.0


def test_calculate_profile_flat_market(engine):
    candles = [
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 500.0},
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 500.0},
    ]
    res = engine.calculate_profile(candles)
    assert res["status"] == "FLAT_MARKET"
    assert res["poc_price"] == 100.0


def test_calculate_profile_valid_distribution(engine):
    # Heavy volume centered around 104-106
    candles = [
        {"open": 100.0, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 100.0},
        {"open": 101.0, "high": 107.0, "low": 104.0, "close": 105.0, "volume": 5000.0}, # Max volume here
        {"open": 105.0, "high": 110.0, "low": 108.0, "close": 109.0, "volume": 200.0},
    ]
    res = engine.calculate_profile(candles)
    assert res["status"] == "VALID"
    assert 104.0 <= res["poc_price"] <= 107.0
    assert res["vah_price"] >= res["poc_price"]
    assert res["val_price"] <= res["poc_price"]
    assert res["current_price_location"] == "ABOVE_VALUE_AREA" # Close is 109, above VAH
