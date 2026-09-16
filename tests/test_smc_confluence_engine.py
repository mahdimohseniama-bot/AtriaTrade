import pytest
from src.core.smc_confluence_engine import (
    SMCConfluenceEngine,
    SMCAction
)


def test_high_confluence_bullish_signal():
    engine = SMCConfluenceEngine(min_confidence_threshold=60.0)
    
    # سناریوی تلاقی فوق‌العاده قوی (100%)
    result = engine.evaluate_setup(
        is_killzone=True,
        has_liquidity_sweep=True,
        has_market_structure_shift=True,
        is_in_ote_zone=True,
        has_order_block=True,
        has_fvg_alignment=True,
        direction="BULLISH",
        entry_price=100.0,
        suggested_sl=95.0,
        suggested_tp=120.0
    )

    assert result.score == 100
    assert result.confidence_pct == 100.0
    assert result.action == SMCAction.STRONG_BUY
    assert len(result.reasons) == 6
    assert result.stop_loss == 95.0
    assert result.take_profit == 120.0


def test_moderate_bearish_signal():
    engine = SMCConfluenceEngine(min_confidence_threshold=60.0)

    # سناریوی تلاقی متوسط (65 درصد)
    result = engine.evaluate_setup(
        is_killzone=True,
        has_liquidity_sweep=True,
        has_market_structure_shift=True,
        is_in_ote_zone=False,
        has_order_block=False,
        has_fvg_alignment=False,
        direction="BEARISH",
        entry_price=200.0,
        suggested_sl=210.0,
        suggested_tp=170.0
    )

    assert result.score == 65
    assert result.confidence_pct == 65.0
    assert result.action == SMCAction.SELL


def test_low_confluence_hold():
    engine = SMCConfluenceEngine(min_confidence_threshold=60.0)

    # سناریوی تلاقی ضعیف که باید فیلتر شود (35%)
    result = engine.evaluate_setup(
        is_killzone=False,
        has_liquidity_sweep=False,
        has_market_structure_shift=True,
        is_in_ote_zone=True,
        has_order_block=False,
        has_fvg_alignment=False,
        direction="BULLISH"
    )

    assert result.score == 35
    assert result.confidence_pct == 35.0
    assert result.action == SMCAction.HOLD


def test_invalid_threshold():
    with pytest.raises(ValueError):
        SMCConfluenceEngine(min_confidence_threshold=150.0)
