from src.core.correlation_manager import CorrelationManager


def test_pearson_correlation():
    manager = CorrelationManager()

    # Perfectly correlated series
    series_a = [100.0, 102.0, 104.0, 106.0, 108.0]
    series_b = [10.0, 10.2, 10.4, 10.6, 10.8]
    assert round(manager.calculate_pearson_correlation(series_a, series_b), 4) == 1.0

    # Perfectly inversely correlated series
    series_c = [50.0, 48.0, 46.0, 44.0, 42.0]
    assert round(manager.calculate_pearson_correlation(series_a, series_c), 4) == -1.0


def test_evaluate_new_trade_risk():
    manager = CorrelationManager(max_allowed_correlation=0.85)

    price_history = {
        "BTCUSDT": [100, 105, 110, 115, 120],
        "ETHUSDT": [10, 10.5, 11.0, 11.5, 12.0],  # Correlation = 1.0 with BTC
        "SOLUSDT": [50, 48, 52, 47, 51]           # Low correlation
    }

    active_positions = {
        "BTCUSDT": {"side": "LONG", "amount": 0.5}
    }

    # Attempting to open LONG ETHUSDT (High correlation -> should be rejected)
    allowed, reason = manager.evaluate_new_trade_risk(
        new_symbol="ETHUSDT",
        new_side="LONG",
        active_positions=active_positions,
        price_history=price_history
    )
    assert not allowed
    assert "High positive correlation" in reason

    # Attempting to open LONG SOLUSDT (Low correlation -> allowed)
    allowed, reason = manager.evaluate_new_trade_risk(
        new_symbol="SOLUSDT",
        new_side="LONG",
        active_positions=active_positions,
        price_history=price_history
    )
    assert allowed
    assert reason is None
