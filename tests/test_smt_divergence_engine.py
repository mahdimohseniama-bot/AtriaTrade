import pytest
from src.core.smt_divergence_engine import SMTDivergenceEngine, SMTType


def test_bullish_smt_primary_lower_low():
    engine = SMTDivergenceEngine(default_boost=0.3)
    # BTC makes Lower Low (60000 -> 59000), ETH makes Higher Low (3000 -> 3050)
    res = engine.detect_divergence(
        primary_asset="BTCUSDT",
        primary_prev_swing=60000.0,
        primary_curr_swing=59000.0,
        correlated_asset="ETHUSDT",
        correlated_prev_swing=3000.0,
        correlated_curr_swing=3050.0,
        swing_type="LOW"
    )
    assert res.divergence_type == SMTType.BULLISH
    assert res.primary_swing == "LL"
    assert res.correlated_swing == "HL"
    assert res.confidence_boost == 0.3


def test_bullish_smt_correlated_lower_low():
    engine = SMTDivergenceEngine()
    # BTC holds Higher Low (60000 -> 60500), ETH makes Lower Low (3000 -> 2900)
    res = engine.detect_divergence(
        primary_asset="BTCUSDT",
        primary_prev_swing=60000.0,
        primary_curr_swing=60500.0,
        correlated_asset="ETHUSDT",
        correlated_prev_swing=3000.0,
        correlated_curr_swing=2900.0,
        swing_type="LOW"
    )
    assert res.divergence_type == SMTType.BULLISH
    assert res.primary_swing == "HL"
    assert res.correlated_swing == "LL"


def test_bearish_smt_primary_higher_high():
    engine = SMTDivergenceEngine(default_boost=0.25)
    # BTC makes Higher High (65000 -> 66000), ETH makes Lower High (3500 -> 3400)
    res = engine.detect_divergence(
        primary_asset="BTCUSDT",
        primary_prev_swing=65000.0,
        primary_curr_swing=66000.0,
        correlated_asset="ETHUSDT",
        correlated_prev_swing=3500.0,
        correlated_curr_swing=3400.0,
        swing_type="HIGH"
    )
    assert res.divergence_type == SMTType.BEARISH
    assert res.primary_swing == "HH"
    assert res.correlated_swing == "LH"
    assert res.confidence_boost == 0.25


def test_bearish_smt_correlated_higher_high():
    engine = SMTDivergenceEngine()
    # BTC makes Lower High (65000 -> 64500), ETH makes Higher High (3500 -> 3600)
    res = engine.detect_divergence(
        primary_asset="BTCUSDT",
        primary_prev_swing=65000.0,
        primary_curr_swing=64500.0,
        correlated_asset="ETHUSDT",
        correlated_prev_swing=3500.0,
        correlated_curr_swing=3600.0,
        swing_type="HIGH"
    )
    assert res.divergence_type == SMTType.BEARISH
    assert res.primary_swing == "LH"
    assert res.correlated_swing == "HH"


def test_no_smt_divergence():
    engine = SMTDivergenceEngine()
    # Both make Higher Highs (Synchronized)
    res = engine.detect_divergence(
        primary_asset="BTCUSDT",
        primary_prev_swing=65000.0,
        primary_curr_swing=67000.0,
        correlated_asset="ETHUSDT",
        correlated_prev_swing=3500.0,
        correlated_curr_swing=3700.0,
        swing_type="HIGH"
    )
    assert res.divergence_type == SMTType.NONE
    assert res.confidence_boost == 0.0
