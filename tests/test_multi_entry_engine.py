import pytest
from src.core.multi_entry_engine import MultiEntryEngine, MultiEntryPosition


def test_multi_tier_weighted_avg_calculation():
    engine = MultiEntryEngine(max_tiers=3, max_total_size=5.0)
    pos = MultiEntryPosition(symbol="BTCUSDT", direction="BUY")

    # پله اول: خرید ۱ واحد در قیمت ۱۰۰
    engine.add_tier(pos, entry_price=100.0, size=1.0, reason="AGGRESSIVE_ENTRY")
    assert pos.total_size == 1.0
    assert pos.weighted_avg_price == 100.0
    assert len(pos.tiers) == 1

    # پله دوم: خرید ۲ واحد در قیمت ۹۰
    engine.add_tier(pos, entry_price=90.0, size=2.0, reason="CONFIRMATION_ENTRY")
    # قیمت میانگین: (100*1 + 90*2) / 3 = 280 / 3 = 93.333333
    assert pos.total_size == 3.0
    assert pos.weighted_avg_price == 93.333333
    assert len(pos.tiers) == 2


def test_unrealized_pnl_buy_and_sell():
    engine = MultiEntryEngine()
    
    # پوزیشن خرید
    buy_pos = MultiEntryPosition(symbol="ETHUSDT", direction="BUY")
    engine.add_tier(buy_pos, entry_price=1000.0, size=2.0)
    assert engine.calculate_unrealized_pnl(buy_pos, current_price=1050.0) == 100.0
    assert engine.calculate_unrealized_pnl(buy_pos, current_price=950.0) == -100.0

    # پوزیشن فروش
    sell_pos = MultiEntryPosition(symbol="ETHUSDT", direction="SELL")
    engine.add_tier(sell_pos, entry_price=1000.0, size=2.0)
    assert engine.calculate_unrealized_pnl(sell_pos, current_price=950.0) == 100.0
    assert engine.calculate_unrealized_pnl(sell_pos, current_price=1050.0) == -100.0


def test_max_tiers_limit_exceeded():
    engine = MultiEntryEngine(max_tiers=2, max_total_size=5.0)
    pos = MultiEntryPosition(symbol="BTCUSDT", direction="BUY")

    engine.add_tier(pos, entry_price=100.0, size=1.0)
    engine.add_tier(pos, entry_price=95.0, size=1.0)

    with pytest.raises(ValueError, match="Cannot exceed maximum allowed tiers"):
        engine.add_tier(pos, entry_price=90.0, size=1.0)


def test_max_total_size_exceeded():
    engine = MultiEntryEngine(max_tiers=3, max_total_size=2.0)
    pos = MultiEntryPosition(symbol="BTCUSDT", direction="BUY")

    engine.add_tier(pos, entry_price=100.0, size=1.5)
    with pytest.raises(ValueError, match="Total position size would exceed limit"):
        engine.add_tier(pos, entry_price=90.0, size=1.0)
