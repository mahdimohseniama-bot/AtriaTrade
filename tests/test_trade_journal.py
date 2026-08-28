import pytest
from src.core.trade_journal import TradeJournal


def test_trade_journal_init_in_memory():
    journal = TradeJournal(db_path=":memory:")
    assert journal.get_trades() == []
    assert journal.get_events() == []


def test_log_trade_and_query():
    journal = TradeJournal(db_path=":memory:")
    trade_id = journal.log_trade(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        price=50000.0,
        volume=0.5,
        slippage_pct=0.001,
        fee=25.0,
        order_id="ORD-101",
        metadata={"strategy": "EMA_Cross"}
    )
    assert trade_id == 1

    trades = journal.get_trades(symbol="BTCUSDT")
    assert len(trades) == 1
    assert trades[0]["symbol"] == "BTCUSDT"
    assert trades[0]["price"] == 50000.0
    assert trades[0]["metadata"]["strategy"] == "EMA_Cross"


def test_log_event_and_query():
    journal = TradeJournal(db_path=":memory:")
    event_id = journal.log_event(
        event_type="CIRCUIT_BREAKER",
        severity="WARNING",
        message="Extreme volatility halt triggered",
        details={"volatility_pct": 0.09}
    )
    assert event_id == 1

    events = journal.get_events(event_type="CIRCUIT_BREAKER")
    assert len(events) == 1
    assert events[0]["severity"] == "WARNING"
    assert events[0]["details"]["volatility_pct"] == 0.09


def test_invalid_trade_inputs():
    journal = TradeJournal(db_path=":memory:")
    with pytest.raises(ValueError, match="Price and volume"):
        journal.log_trade("BTCUSDT", "BUY", "MARKET", -100.0, 1.0)

    with pytest.raises(ValueError, match="Price and volume"):
        journal.log_trade("BTCUSDT", "BUY", "MARKET", 100.0, 0.0)
