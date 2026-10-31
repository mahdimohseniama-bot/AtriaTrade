import pytest
from src.core.wallex_precision_normalizer import WallexPrecisionNormalizer, NormalizedOrderSpec

def test_stage39_precision_quantity_round_down():
    # step_size = 0.0001 (e.g. BTCUSDT)
    normalizer = WallexPrecisionNormalizer()
    spec = normalizer.normalize(
        symbol="BTCUSDT",
        raw_quantity=0.00548999,
        raw_price=67420.738,
        step_size=0.0001,
        tick_size=0.01
    )
    
    assert spec.is_valid is True
    assert spec.normalized_quantity == 0.0054  # must floor/round-down, never round up
    assert spec.normalized_price == 67420.74   # 67420.738 rounded half up to 2 decimals
    assert spec.notional_value == pytest.approx(0.0054 * 67420.74, rel=1e-4)

def test_stage39_precision_sub_minimum_quantity_rejected():
    normalizer = WallexPrecisionNormalizer()
    spec = normalizer.normalize(
        symbol="BTCUSDT",
        raw_quantity=0.00004,  # below step_size of 0.0001
        raw_price=65000.0,
        step_size=0.0001,
        tick_size=0.01,
        min_qty=0.0001
    )
    
    assert spec.is_valid is False
    assert spec.normalized_quantity == 0.0
    assert spec.rejection_reason == "QUANTITY_BELOW_MINIMUM"

def test_stage39_precision_notional_value_min_check():
    normalizer = WallexPrecisionNormalizer()
    # Min notional quote is 5.0 USDT, here quantity * price = 3.0 USDT
    spec = normalizer.normalize(
        symbol="BTCUSDT",
        raw_quantity=0.0001,
        raw_price=30000.0,
        step_size=0.0001,
        tick_size=0.1,
        min_notional=5.0
    )
    
    assert spec.is_valid is False
    assert spec.rejection_reason == "NOTIONAL_BELOW_MINIMUM"
