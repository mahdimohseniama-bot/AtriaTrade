"""
AtriaTrade - Stress Test Suite
"""
import pytest
import math
from unittest.mock import MagicMock, patch


class TestSpikeFilterStress:
    def test_zero_median_division_error(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=3, max_deviation_pct=0.05)
        sf.price_history = [0.0, 0.0, 0.0]
        sf.last_valid_price = 0.0
        result = sf.process_tick(100.0)
        assert result is not None

    def test_nan_price_input(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=3)
        result = sf.process_tick(float('nan'))
        assert result["is_valid"] is False

    def test_negative_price(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=3)
        result = sf.process_tick(-50.0)
        assert result["is_valid"] is False

    def test_very_large_price_jump(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=5, max_deviation_pct=0.05)
        sf.process_tick(100.0)
        result = sf.process_tick(1000000.0)
        assert result["is_valid"] is False

    def test_sanitized_price_not_none(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=3)
        result = sf.process_tick(-1.0)
        assert result["sanitized_price"] is not None
        assert result["sanitized_price"] == 0.0

    def test_rapid_normal_then_spike(self):
        from src.core.spike_filter import SpikeFilter
        sf = SpikeFilter(window_size=5, max_deviation_pct=0.05, confirmation_count=2)
        for p in [100, 101, 99, 100, 102]:
            sf.process_tick(float(p))
        result = sf.process_tick(500.0)
        assert result["is_valid"] is False
        assert result["sanitized_price"] == 102.0


class TestVolatilityRegimeOptimizerStress:
    def test_zero_baseline_atr(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        try:
            result = opt.optimize(current_atr=1.0, baseline_atr=0.0)
            assert result is not None
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError with baseline_atr=0")

    def test_none_atr_values(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        try:
            result = opt.optimize(None, 1.0)
            assert result is not None
        except Exception:
            pytest.fail("optimize() should not crash with None")

    def test_negative_atr_values(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        try:
            result = opt.optimize(-1.0, 1.0)
            assert result is not None
        except Exception:
            pytest.fail("optimize() should not crash with negative ATR")

    def test_nan_atr_values(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        try:
            result = opt.optimize(float('nan'), 1.0)
            assert result is not None
        except Exception:
            pytest.fail("optimize() should not crash with NaN")

    def test_inf_atr_ratio(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        try:
            result = opt.optimize(float('inf'), 1.0)
            assert result is not None
        except Exception:
            pytest.fail("optimize() should not crash with inf")


class TestStrategyAggregatorStress:
    def test_none_trend_input(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator()
        try:
            result = agg.aggregate_signals(None, 0.0, {}, None, 100.0)
            assert result is not None
        except Exception:
            pytest.fail("aggregate_signals() should not crash with None")

    def test_nan_imbalance_input(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator()
        try:
            result = agg.aggregate_signals("BUY", float('nan'), {}, None, 100.0)
            assert result is not None
        except Exception:
            pytest.fail("aggregate_signals() should not crash with NaN")

    def test_empty_string_trend(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator()
        result = agg.aggregate_signals("", 0.0, {}, None, 100.0)
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_extreme_imbalance_values(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator(min_conf=0.35)
        result = agg.aggregate_signals("BUY", 1000000.0, {}, None, 100.0)
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_score_never_exceeds_1(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator(min_conf=0.0)
        result = agg.aggregate_signals("BUY", 0.5, {}, None, 100.0)
        assert result["confidence_score"] <= 1.0


class TestStrategyOrchestratorStress:
    def test_empty_signals_list(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        result = orch.decide([])
        assert result["decision"] == "HOLD"

    def test_none_signals_list(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        try:
            result = orch.decide(None)
            assert result["decision"] == "HOLD"
        except Exception:
            pytest.fail("decide() should not crash with None")

    def test_signal_with_missing_strategy(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"action": "BUY", "confidence": 0.9}]
        try:
            result = orch.decide(signals)
            assert result is not None
        except Exception:
            pytest.fail("decide() should not crash with missing strategy field")

    def test_signal_with_missing_action(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "confidence": 0.9}]
        try:
            result = orch.decide(signals)
            assert result is not None
        except Exception:
            pytest.fail("decide() should not crash with missing action field")

    def test_signal_with_missing_confidence(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "action": "BUY"}]
        try:
            result = orch.decide(signals)
            assert result is not None
        except Exception:
            pytest.fail("decide() should not crash with missing confidence field")

    def test_nan_confidence(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "action": "BUY", "confidence": float('nan')}]
        try:
            result = orch.decide(signals)
            assert result["decision"] in ["BUY", "SELL", "HOLD"]
        except Exception:
            pytest.fail("decide() should not crash with NaN confidence")


class TestTradingPipelineStress:
    def test_none_market_data(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        tp = TradingPipeline(pm, rm, strategy=None, mode="paper")
        try:
            result = tp.process(None)
            assert result is not None
        except Exception:
            pytest.fail("process() should not crash with None")

    def test_invalid_mode(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        try:
            tp = TradingPipeline(pm, rm, strategy=None, mode="invalid_mode")
            assert tp is not None
        except Exception:
            pytest.fail("should not crash with invalid mode")


class TestCircuitBreakerStress:
    def test_threshold_exceeded_halts(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert not cb.halted
        cb.record_failure()
        assert cb.halted

    def test_success_resets_counter(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert not cb.halted

    def test_halted_breaker_still_records(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.halted
        before = cb.failures if hasattr(cb, 'failures') else 0
        cb.record_failure()
        after = cb.failures if hasattr(cb, 'failures') else 0
        assert after >= before
