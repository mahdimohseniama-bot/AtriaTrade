import pytest
from src.core.strategy_orchestrator import StrategyOrchestrator

@pytest.fixture
def orchestrator():
    return StrategyOrchestrator(
        strategy_weights={"smc": 1.0, "technical": 0.6, "orderflow": 0.8},
        min_confidence=0.6,
        min_score=0.3,
    )

def test_consensus_buy_decision(orchestrator):
    signals = [
        {"strategy": "smc", "action": "BUY", "confidence": 0.9},
        {"strategy": "technical", "action": "BUY", "confidence": 0.7},
        {"strategy": "orderflow", "action": "SELL", "confidence": 0.5},  # زیر حد اعتماد، نادیده گرفته می‌شود
    ]
    res = orchestrator.decide(signals)
    assert res["decision"] == "BUY"
    assert res["score"] == pytest.approx(0.9 + 0.6 * 0.7)

def test_conflicting_signals_result_in_hold(orchestrator):
    signals = [
        {"strategy": "smc", "action": "BUY", "confidence": 0.8},      # +0.8
        {"strategy": "orderflow", "action": "SELL", "confidence": 0.8},  # -0.64
    ]
    res = orchestrator.decide(signals)
    assert res["decision"] == "HOLD"  # امتیاز خالص 0.16 زیر آستانه 0.3 است

def test_low_confidence_signals_ignored(orchestrator):
    signals = [
        {"strategy": "smc", "action": "BUY", "confidence": 0.3},  # نادیده
        {"strategy": "technical", "action": "SELL", "confidence": 0.4},  # نادیده
    ]
    res = orchestrator.decide(signals)
    assert res["decision"] == "HOLD"
    assert res["contributing_signals"] == []

def test_unknown_strategy_rejected(orchestrator):
    signals = [{"strategy": "alien", "action": "BUY", "confidence": 0.9}]
    with pytest.raises(ValueError):
        orchestrator.decide(signals)

def test_empty_weights_rejected():
    with pytest.raises(ValueError):
        StrategyOrchestrator(strategy_weights={})
