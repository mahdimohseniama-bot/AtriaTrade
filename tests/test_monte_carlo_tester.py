import pytest
from src.core.monte_carlo_tester import MonteCarloStressTester


def test_monte_carlo_insufficient_history():
    tester = MonteCarloStressTester(initial_capital=1000.0)
    res = tester.run_simulation(trade_returns_pct=[2.5])
    assert res["success"] is False
    assert res["reason"] == "INSUFFICIENT_TRADE_HISTORY"


def test_monte_carlo_profitable_robust_strategy():
    tester = MonteCarloStressTester(initial_capital=10000.0)
    # استراتژی با برتری آماری مشخص (بیشتر معاملات سود ۲ تا ۵ درصد با باخت‌های کوچک)
    trades = [2.0, 3.5, -1.0, 4.0, -1.5, 2.5, 3.0, -0.8, 5.0, 2.0]
    res = tester.run_simulation(trade_returns_pct=trades, num_simulations=200, random_seed=42)
    
    assert res["success"] is True
    assert res["simulations_run"] == 200
    assert res["median_final_equity"] > 10000.0
    assert res["ruin_probability_pct"] == 0.0
    assert res["is_robust"] is True


def test_monte_carlo_fragile_high_risk_strategy():
    tester = MonteCarloStressTester(initial_capital=10000.0)
    # استراتژی بسیار پرریسک با باخت‌های سنگین
    trades = [-15.0, -20.0, 30.0, -25.0, -10.0, 10.0, -30.0]
    res = tester.run_simulation(trade_returns_pct=trades, num_simulations=200, random_seed=42)
    
    assert res["success"] is True
    assert res["p95_max_drawdown_pct"] > 50.0
    assert res["is_robust"] is False
    assert res["ruin_probability_pct"] > 0.0


def test_monte_carlo_seed_determinism():
    tester = MonteCarloStressTester()
    trades = [1.5, -1.0, 2.0, -0.5, 3.0]
    res1 = tester.run_simulation(trades, num_simulations=100, random_seed=123)
    res2 = tester.run_simulation(trades, num_simulations=100, random_seed=123)
    
    assert res1["p95_max_drawdown_pct"] == res2["p95_max_drawdown_pct"]
    assert res1["median_final_equity"] == res2["median_final_equity"]
