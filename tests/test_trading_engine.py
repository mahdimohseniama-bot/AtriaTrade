import pytest
from src.core.trading_engine import TradingEngine
from src.core.portfolio_manager import PortfolioManager
from src.core.risk_manager import RiskManager
from src.core.order_executor import OrderExecutor
from src.core.profit_reserve import ProfitReserveManager

@pytest.fixture
def setup_engine():
    portfolio = PortfolioManager(initial_balance=10000.0)
    risk = RiskManager()
    executor = OrderExecutor(portfolio=portfolio)
    reserve = ProfitReserveManager(portfolio=portfolio)
    engine = TradingEngine(
        portfolio=portfolio,
        risk=risk,
        executor=executor,
        reserve=reserve
    )
    return engine, portfolio, risk, executor, reserve

def test_01_engine_initialization(setup_engine):
    engine, portfolio, risk, executor, reserve = setup_engine
    assert engine is not None
    assert engine.is_running is False
    assert portfolio.get_balance() == 10000.0

def test_02_engine_start_stop(setup_engine):
    engine, _, _, _, _ = setup_engine
    engine.start()
    assert engine.is_running is True
    engine.stop()
    assert engine.is_running is False

def test_03_process_tick_buy_and_sell(setup_engine):
    engine, portfolio, _, _, reserve = setup_engine
    engine.start()
    
    # 1. سیگنال BUY
    tick_buy = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "signal": "BUY",
        "confidence": 0.85
    }
    trade_buy = engine.process_tick(tick_buy)
    assert trade_buy is not None
    assert portfolio.get_position("BTCUSDT") > 0.0

    # 2. سیگنال SELL و سود
    tick_sell = {
        "symbol": "BTCUSDT",
        "price": 55000.0,
        "signal": "SELL",
        "confidence": 0.90
    }
    trade_sell = engine.process_tick(tick_sell)
    assert trade_sell is not None
    assert portfolio.get_position("BTCUSDT") == 0.0
    assert reserve.get_vault_balance() > 0.0

def test_04_process_tick_hold(setup_engine):
    engine, portfolio, _, _, _ = setup_engine
    engine.start()
    
    tick_hold = {
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "signal": "HOLD",
        "confidence": 0.50
    }
    trade = engine.process_tick(tick_hold)
    assert trade is None
    assert portfolio.get_position("BTCUSDT") == 0.0
