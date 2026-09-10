import pytest
from src.core.market_regime import MarketRegimeFilter, MarketRegime
from src.core.portfolio_risk import PortfolioRiskManager
from src.core.paper_live_runner import PaperTradingLiveRunner


@pytest.fixture
def mock_regime_filter():
    return MarketRegimeFilter(fast_window=3, slow_window=5)


@pytest.fixture
def mock_portfolio_risk():
    return PortfolioRiskManager(max_total_exposure_pct=0.5)


@pytest.fixture
def runner(mock_regime_filter, mock_portfolio_risk):
    return PaperTradingLiveRunner(
        symbol="BTC/USDT",
        initial_balance=10000.0,
        regime_filter=mock_regime_filter,
        portfolio_risk=mock_portfolio_risk,
    )


def test_runner_start_stop(runner):
    assert not runner.is_running
    runner.start()
    assert runner.is_running
    runner.stop()
    assert not runner.is_running


def test_runner_ingest_candle_when_stopped(runner):
    candle = {"open": 50000, "high": 50500, "low": 49500, "close": 50200, "volume": 100}
    res = runner.ingest_candle(candle)
    assert res["status"] == "STOPPED"


def test_runner_ingest_candle_when_running(runner):
    runner.start()
    candle = {"open": 50000, "high": 50500, "low": 49500, "close": 50200, "volume": 100}
    res = runner.ingest_candle(candle)
    assert res["status"] == "PROCESSED"
    assert res["current_price"] == 50200.0
    assert len(runner.candles) == 1


def test_process_signal_buy_and_sell(runner):
    runner.start()
    candle = {"open": 50000, "high": 50500, "low": 49500, "close": 50000, "volume": 100}
    runner.ingest_candle(candle)

    buy_sig = {"side": "BUY", "size_pct": 0.2}
    buy_res = runner.process_signal(buy_sig, candle)
    assert buy_res["status"] in ["FILLED", "REJECTED"]

    if buy_res["status"] == "FILLED":
        assert len(runner.open_positions) == 1
        assert runner.balance < 10000.0

        sell_candle = {"open": 51000, "high": 52000, "low": 50900, "close": 52000, "volume": 120}
        runner.ingest_candle(sell_candle)
        sell_sig = {"side": "SELL"}
        sell_res = runner.process_signal(sell_sig, sell_candle)

        assert sell_res["status"] == "CLOSED"
        assert sell_res["pnl"] > 0
        assert len(runner.open_positions) == 0


def test_profit_split_60_40(runner):
    """Verify exact 60% Vault and 40% Compound split on profitable trade."""
    runner.start()
    entry_candle = {"open": 50000, "high": 50000, "low": 50000, "close": 50000, "volume": 10}
    runner.ingest_candle(entry_candle)

    # شبیه‌سازی وضعیت اکانت: ۱۰۰۰ دلار در پوزیشن و ۰ دلار نقدینگی باقی‌مانده
    runner.balance = 0.0
    runner.open_positions.append({
        "symbol": "BTC/USDT",
        "side": "BUY",
        "entry_price": 50000.0,
        "units": 0.02,  # 0.02 * 50000 = 1000$ size
        "size": 1000.0,
    })

    # خروج با سود: قیمت از ۵۰,۰۰۰ به ۵۵,۰۰۰ (۱۰٪ سود = ۱۰۰ دلار PnL)
    exit_candle = {"open": 55000, "high": 55000, "low": 55000, "close": 55000, "volume": 10}
    res = runner.process_signal({"side": "SELL"}, exit_candle)

    assert res["status"] == "CLOSED"
    assert pytest.approx(res["pnl"], 0.001) == 100.0
    assert pytest.approx(res["vault_share"], 0.001) == 60.0    # ۶۰٪ کیف پول ذخیره
    assert pytest.approx(res["compound_share"], 0.001) == 40.0 # ۴۰٪ رشد سرمایه
    assert pytest.approx(runner.vault_balance, 0.001) == 60.0
    assert pytest.approx(runner.balance, 0.001) == 1040.0      # ۱۰۰۰ اصل + ۴۰ کمپاند


def test_process_signal_when_stopped(runner):
    candle = {"open": 50000, "high": 50500, "low": 49500, "close": 50000, "volume": 100}
    buy_sig = {"side": "BUY", "size_pct": 0.2}
    res = runner.process_signal(buy_sig, candle)
    assert res["status"] == "REJECTED"
    assert res["reason"] == "Runner is stopped"
