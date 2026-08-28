import pytest
from src.core.multi_timeframe_confluence import (
    MultiTimeframeConfluenceEngine,
    TimeframeSignal
)


def test_strong_bullish_confluence():
    engine = MultiTimeframeConfluenceEngine(min_confluence_threshold=0.5, min_agreement_ratio=0.6)
    signals = {
        "1h": TimeframeSignal(timeframe="1h", trend_direction=1, momentum_score=0.8, weight=2.0),
        "15m": TimeframeSignal(timeframe="15m", trend_direction=1, momentum_score=0.7, weight=1.5),
        "5m": TimeframeSignal(timeframe="5m", trend_direction=1, momentum_score=0.6, weight=1.0)
    }
    result = engine.evaluate_confluence(signals, trigger_tf="5m")
    assert result.is_trend_aligned is True
    assert result.overall_direction == 1
    assert result.confluence_score > 0.6
    assert result.agreement_ratio == 1.0
    assert result.rejection_reason is None


def test_conflict_counter_trend_rejection():
    engine = MultiTimeframeConfluenceEngine(min_confluence_threshold=0.5, min_agreement_ratio=0.6)
    # تایم بالاتر نزولی است اما تریگر 5 دقیقه صعودی ضعیف است
    signals = {
        "1h": TimeframeSignal(timeframe="1h", trend_direction=-1, momentum_score=-0.8, weight=2.5),
        "15m": TimeframeSignal(timeframe="15m", trend_direction=-1, momentum_score=-0.5, weight=1.5),
        "5m": TimeframeSignal(timeframe="5m", trend_direction=1, momentum_score=0.4, weight=1.0)
    }
    result = engine.evaluate_confluence(signals, trigger_tf="5m")
    assert result.is_trend_aligned is False
    assert result.overall_direction == 0
    assert result.rejection_reason is not None


def test_invalid_confluence_inputs():
    engine = MultiTimeframeConfluenceEngine()
    with pytest.raises(ValueError):
        engine.evaluate_confluence({}, trigger_tf="5m")

    with pytest.raises(ValueError):
        engine.evaluate_confluence({
            "1h": TimeframeSignal(timeframe="1h", trend_direction=5, momentum_score=0.5)
        }, trigger_tf="1h")
