"""
Tests for BacktestPerformance integration.
"""

from src.core.backtest_performance import BacktestPerformance


class FakeBacktestEngine:
    """Fake backtest engine for safe integration testing."""

    def run(self, historical_data, symbol="BTCUSDT"):
        return {
            "initial_capital": 1000.0,
            "final_capital": 1080.0,
            "closed_trades": [
                {
                    "symbol": symbol,
                    "pnl": 50.0,
                    "pnl_percent": 5.0,
                },
                {
                    "symbol": symbol,
                    "pnl": -20.0,
                    "pnl_percent": -2.0,
                },
                {
                    "symbol": symbol,
                    "pnl": 80.0,
                    "pnl_percent": 8.0,
                },
                {
                    "symbol": symbol,
                    "pnl": -30.0,
                    "pnl_percent": -3.0,
                },
            ],
            "equity_curve": [
                1000.0,
                1050.0,
                1030.0,
                1110.0,
                1080.0,
            ],
        }


def test_direct_analysis() -> None:
    """Test analysis of a prepared backtest result."""
    integration = BacktestPerformance(risk_free_rate=0.0)

    result = FakeBacktestEngine().run(
        historical_data=[],
        symbol="BTCUSDT",
    )

    report = integration.analyze(result)

    assert "backtest" in report
    assert "performance" in report

    assert report["backtest"]["initial_capital"] == 1000.0
    assert report["backtest"]["final_capital"] == 1080.0
    assert report["backtest"]["total_trades"] == 4

    performance = report["performance"]

    assert performance["total_trades"] == 4
    assert performance["wins"] == 2
    assert performance["losses"] == 2
    assert performance["win_rate_percent"] == 50.0
    assert performance["profit_factor"] == 2.6
    assert performance["net_profit"] == 80.0
    assert performance["net_profit_percent"] == 8.0


def test_engine_analysis() -> None:
    """Test running an engine and analyzing its output."""
    integration = BacktestPerformance()
    engine = FakeBacktestEngine()

    report = integration.analyze_engine(
        engine=engine,
        historical_data=[],
        symbol="ETHUSDT",
    )

    assert report["backtest"]["total_trades"] == 4
    assert report["backtest"]["closed_trades"][0]["symbol"] == "ETHUSDT"
    assert report["performance"]["profit_factor"] == 2.6


def test_invalid_result() -> None:
    """Test validation of incomplete backtest results."""
    integration = BacktestPerformance()

    try:
        integration.analyze(
            {
                "initial_capital": 1000.0,
                "final_capital": 1000.0,
                "closed_trades": [],
            }
        )
    except ValueError as exc:
        assert "equity_curve" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing equity_curve")


def test_backtest_performance() -> None:
    print("========================================")
    print("START: BacktestPerformance Tests")
    print("========================================")

    test_direct_analysis()
    print("[OK] Direct backtest analysis passed")

    test_engine_analysis()
    print("[OK] Engine analysis passed")

    test_invalid_result()
    print("[OK] Invalid result validation passed")

    print("========================================")
    print("=== BACKTEST PERFORMANCE TEST PASSED ===")
    print("========================================")


if __name__ == "__main__":
    test_backtest_performance()
