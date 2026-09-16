"""
Unit and functional tests for PerformanceAnalyzer.
"""

from src.core.performance_analyzer import PerformanceAnalyzer


def test_performance_analyzer() -> None:
    print("========================================")
    print("START: PerformanceAnalyzer Tests")
    print("========================================")

    analyzer = PerformanceAnalyzer(risk_free_rate=0.0)

    # 1. Test empty trades & flat equity curve
    res_empty = analyzer.analyze(trades=[], equity_curve=[1000.0], initial_capital=1000.0)
    assert res_empty["total_trades"] == 0
    assert res_empty["win_rate_percent"] == 0.0
    assert res_empty["profit_factor"] == 0.0
    assert res_empty["max_drawdown_percent"] == 0.0
    print("[OK] Empty trades handled correctly")

    # 2. Test drawdown calculation
    dd_data = [1000.0, 1200.0, 900.0, 1100.0, 800.0]
    # Peak = 1200, trough = 800 -> DD = (1200 - 800) / 1200 * 100 = 33.3333%
    dd_res = analyzer.calculate_drawdown(dd_data)
    assert abs(dd_res["max_drawdown_percent"] - 33.3333) < 0.01
    assert dd_res["max_drawdown_absolute"] == 400.0
    print("[OK] Max Drawdown math verified")

    # 3. Test Sharpe and Sortino Ratios
    returns_sample = [0.05, -0.02, 0.04, 0.01, -0.01, 0.03]
    sharpe = analyzer.calculate_sharpe_ratio(returns_sample)
    sortino = analyzer.calculate_sortino_ratio(returns_sample)
    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)
    assert sortino >= sharpe  # Downside dev <= total std dev for positive mean
    print(f"[OK] Sharpe ({sharpe}) and Sortino ({sortino}) computed correctly")

    # 4. Test comprehensive analysis with realistic trade list
    sample_trades = [
        {"symbol": "BTCUSDT", "pnl": 50.0, "pnl_percent": 5.0},
        {"symbol": "BTCUSDT", "pnl": -20.0, "pnl_percent": -2.0},
        {"symbol": "BTCUSDT", "pnl": 80.0, "pnl_percent": 8.0},
        {"symbol": "BTCUSDT", "pnl": -30.0, "pnl_percent": -3.0},
    ]
    curve = [1000.0, 1050.0, 1030.0, 1110.0, 1080.0]

    full_res = analyzer.analyze(trades=sample_trades, equity_curve=curve, initial_capital=1000.0)
    assert full_res["total_trades"] == 4
    assert full_res["wins"] == 2
    assert full_res["losses"] == 2
    assert full_res["win_rate_percent"] == 50.0
    # Gross Profit = 130, Gross Loss = 50 -> PF = 130 / 50 = 2.6
    assert full_res["profit_factor"] == 2.6
    assert full_res["net_profit"] == 80.0
    assert full_res["net_profit_percent"] == 8.0
    print(f"[OK] Full summary verified: PF={full_res['profit_factor']}, WinRate={full_res['win_rate_percent']}%")

    print("========================================")
    print("=== PERFORMANCE ANALYZER TEST PASSED ===")
    print("========================================")


if __name__ == "__main__":
    test_performance_analyzer()
