import pytest
from src.strategies.sma_cross_strategy import SMACrossStrategy
from src.core.backtest_engine import BacktestEngine
from src.core.execution_realism import FeeConfig, SlippageConfig, ExecutionRealismModel

def generate_synthetic_candles():
    prices = [100.0, 101.0, 102.5, 101.5, 103.0, 105.0, 107.0, 106.0, 104.0, 102.0, 100.0, 99.0, 101.0, 103.5, 106.0]
    candles = []
    base_time = 1700000000
    for idx, p in enumerate(prices):
        candles.append({
            "timestamp": base_time + (idx * 60),
            "open": p - 0.2,
            "high": p + 0.5,
            "low": p - 0.5,
            "close": p,
            "volume": 10.0
        })
    return candles

def test_strategy_deterministic_crossover():
    strat1 = SMACrossStrategy(symbol="BTCUSDT", short_window=3, long_window=5, quantity=1.0)
    strat2 = SMACrossStrategy(symbol="BTCUSDT", short_window=3, long_window=5, quantity=1.0)
    
    prices = [100.0, 100.5, 101.0, 101.5, 103.0, 104.0, 102.0, 100.0, 99.0, 98.0]
    signals1 = [strat1.generate_signal(p) for p in prices]
    signals2 = [strat2.generate_signal(p) for p in prices]
    
    assert signals1 == signals2
    assert "BUY" in signals1
    assert "SELL" in signals1

def test_execution_realism_cost_deduction():
    fee_cfg = FeeConfig(maker_fee_rate=0.001, taker_fee_rate=0.002)
    slip_cfg = SlippageConfig(slippage_percent=0.0005)
    model = ExecutionRealismModel(fee_config=fee_cfg, slippage_config=slip_cfg)
    
    result = model.apply_realism(price=100.0, quantity=1.0, side="BUY", is_maker=False)
    assert result.executed_price > 100.0
    assert result.fee_amount > 0.0

def test_backtest_engine_run_reproducibility():
    candles = generate_synthetic_candles()
    strat1 = SMACrossStrategy(symbol="BTCUSDT", short_window=3, long_window=5, quantity=0.1)
    engine1 = BacktestEngine(strategy=strat1, initial_capital=1000.0, fee_rate=0.001)
    res1 = engine1.run(candles)
    
    strat2 = SMACrossStrategy(symbol="BTCUSDT", short_window=3, long_window=5, quantity=0.1)
    engine2 = BacktestEngine(strategy=strat2, initial_capital=1000.0, fee_rate=0.001)
    res2 = engine2.run(candles)
    
    assert res1["final_capital"] == res2["final_capital"]
    assert res1["total_trades"] == res2["total_trades"]
