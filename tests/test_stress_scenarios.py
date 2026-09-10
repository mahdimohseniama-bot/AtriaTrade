import pytest
from src.core.market_regime import MarketRegimeFilter
from src.core.portfolio_risk import PortfolioRiskManager
from src.core.paper_live_runner import PaperTradingLiveRunner


@pytest.fixture
def stress_runner():
    regime = MarketRegimeFilter(fast_window=3, slow_window=5)
    risk = PortfolioRiskManager(max_total_exposure_pct=0.8)
    return PaperTradingLiveRunner(
        symbol="BTC/USDT",
        initial_balance=10000.0,
        regime_filter=regime,
        portfolio_risk=risk,
    )


def test_extreme_price_drop_scenario(stress_runner):
    """تست افت شدید و ناگهانی قیمت (Flash Crash)"""
    stress_runner.start()
    
    # ورود اولیه
    entry_candle = {"open": 60000.0, "high": 60500.0, "low": 59500.0, "close": 60000.0, "volume": 500}
    stress_runner.ingest_candle(entry_candle)
    
    buy_sig = {"side": "BUY", "size_pct": 0.3}
    buy_res = stress_runner.process_signal(buy_sig, entry_candle)
    
    if buy_res["status"] == "FILLED":
        # کندل ریزش شدید ۵۰ درصدی
        crash_candle = {"open": 30000.0, "high": 30500.0, "low": 29000.0, "close": 30000.0, "volume": 5000}
        stress_runner.ingest_candle(crash_candle)
        
        sell_res = stress_runner.process_signal({"side": "SELL"}, crash_candle)
        assert sell_res["status"] == "CLOSED"
        assert sell_res["pnl"] < 0
        assert stress_runner.balance > 0  # نباید حساب منفی شود


def test_high_frequency_candle_feed(stress_runner):
    """تست ورود حجم بالای کندل‌ها بدون کرش"""
    stress_runner.start()
    base_price = 50000.0
    for i in range(100):
        c = {
            "open": base_price + i,
            "high": base_price + i + 10,
            "low": base_price + i - 10,
            "close": base_price + i + 5,
            "volume": 100 + i
        }
        res = stress_runner.ingest_candle(c)
        assert res["status"] == "PROCESSED"
    
    assert len(stress_runner.candles) == 100


def test_rapid_consecutive_signals(stress_runner):
    """تست ارسال متوالی و سریع سیگنال‌ها"""
    stress_runner.start()
    candle = {"open": 50000.0, "high": 50500.0, "low": 49500.0, "close": 50000.0, "volume": 100}
    stress_runner.ingest_candle(candle)

    # سیگنال اول خرید
    sig1 = {"side": "BUY", "size_pct": 0.2}
    res1 = stress_runner.process_signal(sig1, candle)
    
    # تلاش برای ارسال مکرر بدون تغییر وضعیت
    sig2 = {"side": "BUY", "size_pct": 0.2}
    res2 = stress_runner.process_signal(sig2, candle)
    
    assert res1["status"] in ["FILLED", "REJECTED"]
    assert res2["status"] in ["FILLED", "REJECTED"]
