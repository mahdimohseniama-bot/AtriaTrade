import pytest
from src.core.strategy_conflict_resolver import StrategyConflictResolver


def test_empty_signals_returns_hold():
    resolver = StrategyConflictResolver()
    res = resolver.resolve("BTCUSDT", [])
    assert res["action"] == "HOLD"
    assert res["has_conflict"] is False


def test_unanimous_buy_resolution():
    resolver = StrategyConflictResolver(min_net_score=0.20)
    signals = [
        {"strategy_name": "SMC", "direction": "BUY", "confidence": 0.8, "weight": 1.0},
        {"strategy_name": "Trend", "direction": "BUY", "confidence": 0.9, "weight": 1.0}
    ]
    res = resolver.resolve("BTCUSDT", signals)
    assert res["action"] == "BUY"
    assert res["net_score"] > 0.5
    assert res["has_conflict"] is False


def test_unanimous_sell_resolution():
    resolver = StrategyConflictResolver(min_net_score=0.20)
    signals = [
        {"strategy_name": "SMC", "direction": "SELL", "confidence": 0.85, "weight": 1.0},
        {"strategy_name": "OrderFlow", "direction": "SELL", "confidence": 0.75, "weight": 1.0}
    ]
    res = resolver.resolve("ETHUSDT", signals)
    assert res["action"] == "SELL"
    assert res["net_score"] < -0.5
    assert res["has_conflict"] is False


def test_hard_conflict_blocks_trade():
    # SMC says BUY (high conf), Trend says SELL (high conf) -> should reject
    resolver = StrategyConflictResolver(disagreement_tolerance=0.35)
    signals = [
        {"strategy_name": "SMC", "direction": "BUY", "confidence": 0.8, "weight": 1.0},
        {"strategy_name": "Trend", "direction": "SELL", "confidence": 0.7, "weight": 1.0}
    ]
    res = resolver.resolve("BTCUSDT", signals)
    assert res["action"] == "HOLD"
    assert res["has_conflict"] is True
    assert "Severe strategy conflict" in res["reason"]


def test_weak_opposition_overridden():
    # Strong Buy with very weak/negligible Sell -> Buy is approved
    resolver = StrategyConflictResolver(min_net_score=0.25, disagreement_tolerance=0.35)
    signals = [
        {"strategy_name": "SMC", "direction": "BUY", "confidence": 0.9, "weight": 2.0},
        {"strategy_name": "Trend", "direction": "BUY", "confidence": 0.85, "weight": 1.0},
        {"strategy_name": "Experimental", "direction": "SELL", "confidence": 0.2, "weight": 0.5}
    ]
    res = resolver.resolve("BTCUSDT", signals)
    assert res["action"] == "BUY"
    assert res["has_conflict"] is False


def test_invalid_direction_raises():
    resolver = StrategyConflictResolver()
    signals = [{"strategy_name": "SMC", "direction": "INVALID", "confidence": 0.8}]
    with pytest.raises(ValueError):
        resolver.resolve("BTCUSDT", signals)


def test_invalid_init_parameters():
    with pytest.raises(ValueError):
        StrategyConflictResolver(min_net_score=-0.1)
    with pytest.raises(ValueError):
        StrategyConflictResolver(disagreement_tolerance=1.5)
