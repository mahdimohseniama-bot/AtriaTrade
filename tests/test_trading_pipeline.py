"""
Tests for TradingPipeline - AtriaTrade
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.portfolio_manager import PortfolioManager
from src.core.recovery_manager import RecoveryManager
from src.core.trading_pipeline import TradingPipeline


def build_pipeline(strategy=None, **kwargs):
    portfolio = PortfolioManager()
    recovery = RecoveryManager(
        max_drawdown_pct=20.0,
        recovery_target_pct=5.0,
        cooldown_cycles=2,
        mode=kwargs.get("mode", "paper"),
    )

    pipeline = TradingPipeline(
        portfolio_manager=portfolio,
        recovery_manager=recovery,
        strategy=strategy,
        mode=kwargs.get("mode", "paper"),
    )

    return pipeline


def test_initialization():
    pipeline = build_pipeline()

    status = pipeline.get_status()

    assert pipeline.mode == "paper"
    assert status["cycle"] == 0
    assert status["running"] is False
    assert status["real_trading_enabled"] is False
    assert status["order_submitted"] is False

    print("PASS: test_initialization")


def test_hold_signal():
    pipeline = build_pipeline()

    result = pipeline.process_cycle(
        {
            "symbol": "BTCUSDT",
            "price": 50000,
            "signal": "HOLD",
            "drawdown_pct": 2,
        }
    )

    assert result["signal"] == "HOLD"
    assert result["decision"] == "HOLD"
    assert result["order_submitted"] is False

    print("PASS: test_hold_signal")


def test_simulated_buy():
    pipeline = build_pipeline()

    result = pipeline.process_cycle(
        {
            "symbol": "BTCUSDT",
            "price": 50000,
            "signal": "BUY",
            "quantity": 0.001,
            "position_weight_pct": 5,
            "drawdown_pct": 2,
        }
    )

    assert result["signal"] == "BUY"
    assert result["decision"] == "SIMULATED_BUY"
    assert result["order_submitted"] is False
    assert result["real_trading_enabled"] is False

    print("PASS: test_simulated_buy")


def test_strategy_callback():
    def strategy(market_data):
        if market_data["price"] > 100:
            return "SELL"
        return "HOLD"

    pipeline = build_pipeline(strategy=strategy)

    result = pipeline.process_cycle(
        {
            "symbol": "ETHUSDT",
            "price": 200,
            "drawdown_pct": 1,
        }
    )

    assert result["signal"] == "SELL"
    assert result["decision"] == "SIMULATED_SELL"

    print("PASS: test_strategy_callback")


def test_recovery_blocks_signal():
    pipeline = build_pipeline()

    result = pipeline.process_cycle(
        {
            "symbol": "BTCUSDT",
            "price": 50000,
            "signal": "BUY",
            "drawdown_pct": 25,
        }
    )

    assert result["recovery_status"] == "critical"
    assert result["decision"] == "BLOCKED_RECOVERY"
    assert result["order_submitted"] is False

    print("PASS: test_recovery_blocks_signal")


def test_batch_run():
    pipeline = build_pipeline()

    results = pipeline.run(
        [
            {
                "symbol": "BTCUSDT",
                "price": 50000,
                "signal": "HOLD",
                "drawdown_pct": 1,
            },
            {
                "symbol": "BTCUSDT",
                "price": 51000,
                "signal": "BUY",
                "drawdown_pct": 1,
                "position_weight_pct": 5,
            },
        ]
    )

    assert len(results) == 2
    assert pipeline.cycle == 2
    assert pipeline.running is False
    assert results[0]["decision"] == "HOLD"
    assert results[1]["decision"] == "SIMULATED_BUY"

    print("PASS: test_batch_run")


def test_invalid_mode():
    portfolio = PortfolioManager()
    recovery = RecoveryManager()

    try:
        TradingPipeline(
            portfolio_manager=portfolio,
            recovery_manager=recovery,
            mode="live",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for live mode")

    print("PASS: test_invalid_mode")


def test_safe_error_handling():
    class BrokenRecovery:
        def evaluate(self, drawdown):
            raise RuntimeError("test recovery error")

    pipeline = TradingPipeline(
        portfolio_manager=PortfolioManager(),
        recovery_manager=BrokenRecovery(),
        mode="paper",
    )

    result = pipeline.process_cycle(
        {
            "symbol": "BTCUSDT",
            "price": 50000,
            "signal": "BUY",
        }
    )

    assert result["decision"] == "ERROR_SAFE_HOLD"
    assert result["signal"] == "HOLD"
    assert result["order_submitted"] is False
    assert pipeline.error_count == 1

    print("PASS: test_safe_error_handling")


if __name__ == "__main__":
    print("START: TradingPipeline Tests")

    test_initialization()
    test_hold_signal()
    test_simulated_buy()
    test_strategy_callback()
    test_recovery_blocks_signal()
    test_batch_run()
    test_invalid_mode()
    test_safe_error_handling()

    print("ALL TradingPipeline TESTS PASSED SUCCESSFULLY!")
