"""
Comprehensive tests for AtriaTrade BacktestEngine.

Simulation-only tests:
- no exchange API
- no real order
- no real trading
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest_engine import BacktestEngine
from src.strategies.sma_cross_strategy import SMACrossStrategy


class SequenceStrategy:
    """Deterministic strategy for testing exact backtest behavior."""

    def __init__(self, signals):
        self.signals = list(signals)
        self.calls = 0
        self.received_price_lengths = []

    def generate_signal(self, prices):
        self.received_price_lengths.append(len(prices))

        if self.calls >= len(self.signals):
            signal = "HOLD"
        else:
            signal = self.signals[self.calls]

        self.calls += 1
        return signal


def make_candles(closes):
    """Create minimal valid OHLCV candles from close prices."""
    return [
        {
            "timestamp": 1600000000 + (index * 60),
            "open": float(price),
            "high": float(price),
            "low": float(price),
            "close": float(price),
            "volume": 10.0,
        }
        for index, price in enumerate(closes)
    ]


def test_backtest_engine_smoke_test():
    """Verify SMA strategy can run end-to-end through the engine."""
    strategy = SMACrossStrategy(short_window=2, long_window=4)
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000.0,
        fee_rate=0.001,
    )

    historical_data = make_candles([
        100.0,
        101.0,
        102.0,
        103.0,
        105.0,
        102.5,
        99.5,
        98.5,
    ])

    summary = engine.run(historical_data, symbol="BTCUSDT")

    assert summary["initial_capital"] == 1000.0
    assert isinstance(summary["final_capital"], float)
    assert isinstance(summary["net_profit"], float)
    assert "total_trades" in summary
    assert "win_rate_percent" in summary
    assert "max_drawdown_percent" in summary
    assert "closed_trades" in summary
    assert "equity_curve" in summary


def test_buy_sell_applies_entry_and_exit_fees_correctly():
    """Both entry and exit fees must be deducted from final capital."""
    strategy = SequenceStrategy([
        "HOLD",
        "BUY",
        "HOLD",
        "SELL",
        "HOLD",
    ])

    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000.0,
        fee_rate=0.001,
    )

    summary = engine.run(
        make_candles([100.0, 110.0, 120.0, 90.0, 95.0]),
        symbol="BTCUSDT",
    )

    expected_entry_fee = 1.0
    expected_quantity = 999.0 / 110.0
    expected_gross_return = expected_quantity * 90.0
    expected_exit_fee = expected_gross_return * 0.001
    expected_final_capital = expected_gross_return - expected_exit_fee

    assert summary["total_trades"] == 1
    assert summary["wins"] == 0
    assert summary["losses"] == 1
    assert summary["final_capital"] == pytest.approx(
        expected_final_capital,
        abs=1e-8,
    )

    trade = summary["closed_trades"][0]

    assert trade["entry_price"] == 110.0
    assert trade["exit_price"] == 90.0
    assert trade["entry_fee"] == pytest.approx(expected_entry_fee)
    assert trade["exit_fee"] == pytest.approx(expected_exit_fee)
    assert trade["gross_return"] == pytest.approx(expected_gross_return)
    assert trade["net_return"] == pytest.approx(expected_final_capital)
    assert trade["pnl"] == pytest.approx(expected_final_capital - 1000.0)


def test_open_position_is_closed_at_last_candle():
    """An unclosed position must be safely closed at the final candle."""
    strategy = SequenceStrategy([
        "BUY",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
    ])

    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000.0,
        fee_rate=0.001,
    )

    summary = engine.run(
        make_candles([100.0, 102.0, 104.0, 106.0, 108.0]),
        symbol="ETHUSDT",
    )

    assert summary["total_trades"] == 1
    assert engine.position is None

    trade = summary["closed_trades"][0]

    assert trade["symbol"] == "ETHUSDT"
    assert trade["entry_price"] == 100.0
    assert trade["exit_price"] == 108.0
    assert trade["closed_at_end"] is True
    assert summary["final_capital"] > 1000.0


def test_engine_only_passes_available_prices_to_strategy():
    """Prevent look-ahead bias: strategy only sees candles up to now."""
    strategy = SequenceStrategy([
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
    ])

    engine = BacktestEngine(strategy=strategy)

    engine.run(
        make_candles([100.0, 101.0, 102.0, 103.0, 104.0]),
        symbol="BTCUSDT",
    )

    assert strategy.received_price_lengths == [1, 2, 3, 4, 5]


def test_max_drawdown_uses_equity_curve():
    """Drawdown must reflect the largest peak-to-trough equity decline."""
    strategy = SequenceStrategy([
        "BUY",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
    ])

    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000.0,
        fee_rate=0.0,
    )

    summary = engine.run(
        make_candles([100.0, 120.0, 80.0, 90.0, 90.0]),
        symbol="BTCUSDT",
    )

    assert summary["equity_curve"] == [
        1000.0,
        1000.0,
        1200.0,
        800.0,
        900.0,
        900.0,
    ]
    assert summary["max_drawdown_percent"] == pytest.approx(
        33.33333333,
        abs=1e-8,
    )


@pytest.mark.parametrize(
    "historical_data, expected_exception, message",
    [
        (None, TypeError, "historical_data must be a list"),
        ([], ValueError, "At least 5 historical candles"),
        (make_candles([100.0, 101.0, 102.0, 103.0]), ValueError,
         "At least 5 historical candles"),
        (
            [
                {"close": 100.0},
                {"close": 101.0},
                {"close": 102.0},
                {"close": 103.0},
                {"close": 0.0},
            ],
            ValueError,
            "Candle close must be greater than zero",
        ),
        (
            [
                {"close": 100.0},
                {"close": 101.0},
                {"close": 102.0},
                {"close": 103.0},
                {"open": 104.0},
            ],
            ValueError,
            "must contain a close",
        ),
    ],
)
def test_invalid_historical_data_is_rejected(
    historical_data,
    expected_exception,
    message,
):
    """Invalid input must fail safely and clearly."""
    engine = BacktestEngine(
        strategy=SequenceStrategy(["HOLD"] * 5),
    )

    with pytest.raises(expected_exception, match=message):
        engine.run(historical_data)


def test_run_resets_previous_state():
    """A second backtest must not reuse trades or capital from the first."""
    strategy = SequenceStrategy([
        "BUY",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
    ])

    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000.0,
        fee_rate=0.0,
    )

    first_result = engine.run(
        make_candles([100.0, 110.0, 120.0, 130.0, 140.0]),
    )

    second_strategy = SequenceStrategy([
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
        "HOLD",
    ])
    engine.strategy = second_strategy

    second_result = engine.run(
        make_candles([100.0, 100.0, 100.0, 100.0, 100.0]),
    )

    assert first_result["final_capital"] == 1400.0
    assert second_result["initial_capital"] == 1000.0
    assert second_result["final_capital"] == 1000.0
    assert second_result["total_trades"] == 0
    assert second_result["closed_trades"] == []
