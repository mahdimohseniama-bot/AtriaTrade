import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.market_regime import MarketRegimeFilter, MarketRegime


def make_candle(close_price: float, high: float = None, low: float = None):
    return {
        "timestamp": 1600000000,
        "open": close_price,
        "high": high or close_price + 1.0,
        "low": low or close_price - 1.0,
        "close": close_price,
        "volume": 100.0
    }


def test_runner_initial_state():
    runner = PaperTradingLiveRunner(initial_balance=5000.0)
    assert runner.balance == 5000.0
    assert not runner.is_running
    
    # تست دریافت کندل در حالت غیرفعال
    res = runner.ingest_candle(make_candle(100.0))
    assert res["status"] == "STOPPED"


def test_runner_start_stop():
    runner = PaperTradingLiveRunner()
    runner.start()
    assert runner.is_running
    
    res = runner.ingest_candle(make_candle(100.0))
    assert res["status"] == "PROCESSED"
    assert res["current_price"] == 100.0
    
    runner.stop()
    assert not runner.is_running


def test_runner_regime_filtering_buy():
    # ساخت فیلتری که روند صعودی دارد و BUY را مجاز می‌داند
    rf = MarketRegimeFilter(fast_window=2, slow_window=4)
    runner = PaperTradingLiveRunner(initial_balance=10000.0, regime_filter=rf)
    runner.start()
    
    # تزریق کندل‌های صعودی
    prices = [100.0, 102.0, 105.0, 110.0, 115.0]
    for p in prices:
        runner.ingest_candle(make_candle(p))
        
    candle = make_candle(115.0)
    
    # سیگنال خرید در روند صعودی باید FILL شود
    buy_res = runner.process_signal({"side": "BUY", "size_pct": 0.1}, candle)
    assert buy_res["status"] == "FILLED"
    assert buy_res["side"] == "BUY"
    assert len(runner.open_positions) == 1


def test_runner_position_lifecycle():
    # فیلتر با استراتژی که در حالت BULLISH خرید و فروش را مجاز می‌کند
    rf = MarketRegimeFilter(fast_window=2, slow_window=4)
    runner = PaperTradingLiveRunner(initial_balance=10000.0, regime_filter=rf)
    runner.start()
    
    # کندل‌های صعودی
    for p in [100.0, 105.0, 110.0, 115.0]:
        runner.ingest_candle(make_candle(p))
        
    candle = make_candle(115.0)
    
    # ۱. ثبت سفارش خرید
    buy_res = runner.process_signal({"side": "BUY", "size_pct": 0.2}, candle)
    assert buy_res["status"] == "FILLED"
    assert runner.balance == 8000.0
    
    # ۲. ثبت سیگنال فروش در قیمت بالاتر (سود)
    sell_candle = make_candle(138.0) # ۲۰ درصد رشد
    # کندل‌های جدید صعودی
    runner.ingest_candle(sell_candle)
    
    sell_res = runner.process_signal({"side": "SELL"}, sell_candle)
    assert sell_res["status"] == "CLOSED"
    assert sell_res["pnl"] > 0
    assert runner.balance > 10000.0
    assert len(runner.open_positions) == 0
