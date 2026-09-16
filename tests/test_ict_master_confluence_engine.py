import pytest
from src.core.ict_master_confluence_engine import (
    ICTMasterConfluenceEngine,
    SetupGrade,
)


def test_perfect_a_plus_setup():
    engine = ICTMasterConfluenceEngine(min_score_threshold=60.0)
    result = engine.evaluate_setup(
        symbol="BTC/USDT",
        direction="BUY",
        has_mss=True,            # 30
        has_fvg=True,            # 20
        has_order_block=True,     # 20
        has_liquidity_sweep=True, # 15
        has_liquidity_void=True   # 15 => Total 100
    )
    assert result.total_score == 100.0
    assert result.grade == SetupGrade.A_PLUS
    assert result.is_valid_entry is True
    assert len(result.factors_met) == 5


def test_grade_b_valid_setup():
    engine = ICTMasterConfluenceEngine(min_score_threshold=60.0)
    # MSS (30) + FVG (20) + Sweep (15) = 65 -> Grade B
    result = engine.evaluate_setup(
        symbol="ETH/USDT",
        direction="SELL",
        has_mss=True,
        has_fvg=True,
        has_liquidity_sweep=True,
    )
    assert result.total_score == 65.0
    assert result.grade == SetupGrade.B
    assert result.is_valid_entry is True


def test_grade_c_below_threshold():
    engine = ICTMasterConfluenceEngine(min_score_threshold=60.0)
    # FVG (20) + OB (20) = 40 -> Grade C
    result = engine.evaluate_setup(
        symbol="PAXG/USDT",
        direction="BUY",
        has_fvg=True,
        has_order_block=True,
    )
    assert result.total_score == 40.0
    assert result.grade == SetupGrade.C
    assert result.is_valid_entry is False


def test_invalid_grade_setup():
    engine = ICTMasterConfluenceEngine()
    result = engine.evaluate_setup(
        symbol="BTC/USDT",
        direction="BUY",
        has_liquidity_sweep=True # 15 -> Invalid
    )
    assert result.total_score == 15.0
    assert result.grade == SetupGrade.INVALID
    assert result.is_valid_entry is False


def test_invalid_inputs_raise_errors():
    with pytest.raises(ValueError):
        ICTMasterConfluenceEngine(min_score_threshold=120.0)

    engine = ICTMasterConfluenceEngine()
    with pytest.raises(ValueError):
        engine.evaluate_setup(symbol="BTC/USDT", direction="HOLD")
