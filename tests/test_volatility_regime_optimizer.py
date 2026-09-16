import pytest
from src.core.volatility_regime_optimizer import (
    VolatilityRegimeOptimizer,
    VolatilityRegime
)


def test_normal_volatility():
    optimizer = VolatilityRegimeOptimizer(base_sl_atr_mult=1.5, base_tp_atr_mult=3.0)
    result = optimizer.optimize(current_atr=10.0, baseline_atr=10.0)
    assert result.regime == VolatilityRegime.NORMAL
    assert result.volatility_ratio == 1.0
    assert result.dynamic_sl_multiplier == 1.5
    assert result.dynamic_tp_multiplier == 3.0
    assert result.risk_size_multiplier == 1.0
    assert result.is_safe_to_enter is True


def test_extreme_volatility_protection():
    optimizer = VolatilityRegimeOptimizer(extreme_vol_threshold=2.0)
    result = optimizer.optimize(current_atr=25.0, baseline_atr=10.0)
    assert result.regime == VolatilityRegime.EXTREME
    assert result.volatility_ratio == 2.5
    assert result.is_safe_to_enter is False
    assert result.risk_size_multiplier <= 0.5
    assert "غیرعادی" in result.warning_message


def test_low_volatility_tightening():
    optimizer = VolatilityRegimeOptimizer(base_sl_atr_mult=2.0, low_vol_threshold=0.6)
    result = optimizer.optimize(current_atr=5.0, baseline_atr=10.0)
    assert result.regime == VolatilityRegime.LOW
    assert result.volatility_ratio == 0.5
    assert result.dynamic_sl_multiplier < 2.0


def test_invalid_atr_inputs():
    optimizer = VolatilityRegimeOptimizer()
    with pytest.raises(ValueError):
        optimizer.optimize(current_atr=-1.0, baseline_atr=10.0)

    with pytest.raises(ValueError):
        optimizer.optimize(current_atr=10.0, baseline_atr=0.0)
