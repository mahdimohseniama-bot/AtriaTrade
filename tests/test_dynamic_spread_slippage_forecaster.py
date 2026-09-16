import pytest
from src.core.dynamic_spread_slippage_forecaster import (
    DynamicSpreadSlippageForecaster,
    MarketMicrostructureState
)


def test_standard_market_forecast():
    forecaster = DynamicSpreadSlippageForecaster(
        base_slippage_pct=0.05,
        max_acceptable_friction_pct=0.50
    )
    state = MarketMicrostructureState(
        bid_price=100.0,
        ask_price=100.1,
        order_size=10.0,
        depth_volume_top=100.0,
        volatility_ratio=1.0,
        is_high_impact_news_window=False
    )
    forecast = forecaster.forecast_slippage(state)
    assert forecast.is_execution_safe is True
    assert forecast.quoted_spread_pct > 0.0
    assert forecast.expected_slippage_pct >= 0.05
    assert forecast.execution_cost_usd > 0.0


def test_high_slippage_low_liquidity():
    forecaster = DynamicSpreadSlippageForecaster(
        base_slippage_pct=0.05,
        max_acceptable_friction_pct=0.30
    )
    # سفارش بزرگ در عمق بسیار کم
    state = MarketMicrostructureState(
        bid_price=100.0,
        ask_price=100.5,
        order_size=200.0,
        depth_volume_top=20.0,
        volatility_ratio=2.5,
        is_high_impact_news_window=True
    )
    forecast = forecaster.forecast_slippage(state)
    assert forecast.is_execution_safe is False
    assert "اصطکاک بیش از حد مجاز" in forecast.penalty_reason


def test_invalid_microstructure_inputs():
    forecaster = DynamicSpreadSlippageForecaster()
    with pytest.raises(ValueError):
        forecaster.forecast_slippage(MarketMicrostructureState(
            bid_price=-10.0, ask_price=100.0, order_size=1.0, depth_volume_top=10.0
        ))

    with pytest.raises(ValueError):
        forecaster.forecast_slippage(MarketMicrostructureState(
            bid_price=105.0, ask_price=100.0, order_size=1.0, depth_volume_top=10.0
        ))
