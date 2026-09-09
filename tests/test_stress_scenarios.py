"""
AtriaTrade - Stress Test Suite (Rewritten v2)
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
        try:
            result = sf.process_tick(100.0)
            assert result is not None
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError with zero-median price history")

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
        fromOptimizerStress:
    def test_zero_baseline_atr(self):
        from opt = VolatilityRegimeOptimizer()
        with pytest.raises(ValueError):
            opt.optimize(current_atr=1.0, baseline_atr=0.0)

    def test_none_atr_values(self):
        from.0)

    def test_none_atr_values(self):
        from        opt = VolatilityRegimeOptimizer()
        with pytest.raises((TypeError, ValueError)):
            opt.optimize(None, 1.0)

    def test_negative_atr_values(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        with pytest.raises(ValueError):
            opt.optimize(-1.0, 1.0)

    def test_nan_atr_values(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        with pytest.raises((TypeError, ValueError)):
            opt.optimize(float('nan'), 1.0)

    def test_inf_atr_ratio(self):
        from src.core.volatility_regime_optimizer import VolatilityRegimeOptimizer
        opt = VolatilityRegimeOptimizer()
        result = opt.optimize(float('inf'), 1.0)
        assert result is not None
        assert result.is_safe_to_enter is False


class TestStrategyAggregatorStress:
    def test_none_trend_input(self):
        from_none_trend_input(self):
        from src.core.strategy_aggregator import StrategyAg()
        result = agg.aggregate_signals(None, 0.0, {}, None, 100.0)
        assert result is not None
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_nan_imbalance_input(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator()
        result = agg.aggregate_signals("BUY", float('nan'), {}, None, 100.0)
        assert result is not None
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_empty_string_trend(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator()
        result = agg.aggregate_signals("", 0.0, {}, None, 100.0)
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_extreme_imbalance_values(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator(min_confidence_score=0.35)
        result = agg.aggregate_signals("BUY", 1000000.0, {}, None, 100.0)
        assert result["action"] in ["BUY", "SELL", "HOLD"]

    def test_score_never_exceeds_1(self):
        from src.core.strategy_aggregator import StrategyAggregator
        agg = StrategyAggregator(min_confidence_score=0.0)
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
        with pytest.raises(TypeError):
            orch.decide(None)

    def test_signal_with_missing_strategy(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"action": "BUY", "confidence": 0.9}]
        with pytest.raises(ValueError):
            orch.decide(signals)

    def test_signal_with_missing_action(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "confidence": 0.9}]
        with pytest.raises(ValueError):
            orch.decide(signals)

    def test_signal_with_missing_confidence(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "action": "BUY"}]
        result =": "A", "action": "BUY"}]
        result = orch.decide(sign"] == "HOLD"

    def test_nan_confidence(self):
        from src.core.strategy_orchestrator import StrategyOrchestrator
        orch = StrategyOrchestrator(strategy_weights={"A": 1.0})
        signals = [{"strategy": "A", "action": "BUY", "confidence": float('nan')}]
        with pytest.raises(ValueError):
           nan')}]
        with pytest.raises(ValueError):
            orch.decide(sign def test_none_market_data(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        rm.evaluate.return_value = {"status": "normal"}
        tp = TradingPipeline(pm, rm, strategy=None, mode="paper")
        with pytest.raises(TypeError):
            tp.process_cycle(None)

    def test_invalid_mode(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        with pytest.raises(ValueError):
            TradingPipeline(pm, rm, strategy=None, mode="invalid_mode")

    def test_none_portfolio_manager_raises(self):
        from src.core.trading_pipeline import TradingPipeline
        rm = MagicMock()
        with pytest.raises(ValueError):
            TradingPipeline(None, rm, mode="paper")

    def test_none_recovery_manager_raises(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        with pytest.raises(ValueError):
            TradingPipeline(pm, None, mode="paper")

    def test_process_cycle_normal_flow(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        rm.evaluate.return_value = {"status": "normal"}
        tp = TradingPipeline(pm, rm, strategy=None, mode="paper")
        result = tp.process_cycle({"symbol": "BTCUSDT", "price": 50000.0, "signal": "BUY"})
        assert result is not None
        assert result["order_submitted"] is False
        assert result["real_trading_enabled"] is False

    def test_get_status(self):
        from src.core.trading_pipeline import TradingPipeline
        pm = MagicMock()
        rm = MagicMock()
        tp = TradingPipeline(pm, rm, mode="paper")
        status = tp.get_status()
        assert status["mode"] == "paper"
        assert status["cycle"] == 0
        assert status["order_submitted"] is False


class TestCircuitBreakerStress:
    def test_threshold_exceeded_halts(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_consecutive_failures=3)
        cb.record_execution_result(False, "err1")
        cb.record_execution_result(False, "err2")
        assert not cb.is_halted
        cb.record_execution_result(False, "err3")
        assert cb.is_halted

    def test_success_resets_counter(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_consecutive_failures=3)
        cb.record_execution_result(False, "err1")
       1")
        cb.record_execution_result(False, "err2")
        cb.record_execution_result assert not cb.is_halted

    def test_halted_breaker_still_records(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_consecutive_failures=2)
        cb.record_execution_result(False, "err1")
        cb.record_execution_result(False, "err2")
        assert cb.is_halted
        before = cb.get_status()["consecutive_failures"]
        cb.record_execution_result(False, "err3")
        after = cb.get_status()["consecutive_failures"]
        assert after >= before

    def test_evaluate_market_conditions_volatility(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(volatility_threshold_pct=0.08)
        safe = cb.evaluate_market_conditions(price_change_pct=0.10, current_drawdown_pct=0.01)
        assert safe is False
        assert cb.is_halted

    def test_evaluate_market_conditions_drawdown(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_drawdown_pct_halt=0.05)
        safe = cb.evaluate_market_conditions(price_change_pct=0.01, current_drawdown_pct=0.06)
        assert safe is False
        assert cb.is_halted

    def test_reset_clears_halt(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_consecutive_failures=2)
        cb.record_execution_result(False, "err1")
        cb.record_execution_result(False, "err2")
        assert cb.is_halted
        cb.reset(manual=True)
        assert not(manual=True)
        assert not cb.is_halted
        assertures"] == 0

    def test_get_status_structure(self):
        from src.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(max_consecutive_failures=5, max_drawdown_pct_halt=0.1)
        status = cb.get_status()
        assert "is_halted" in status
        assert "halt_reason" in status
        assert "consecutive_failures" in status
        assert "max_consecutive_failures" in status
        assert status["max_consecutive_failures"] == 5
