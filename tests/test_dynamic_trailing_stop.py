from src.core.dynamic_trailing_stop import DynamicTrailingStop


def test_long_trailing_stop_activation_and_trail():
    # Long @ $100, activation at +2% ($102), ATR multiplier = 2.0
    tracker = DynamicTrailingStop(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=100.0,
        activation_pct=0.02,
        atr_multiplier=2.0
    )

    # Price moves to 101 -> not activated yet (needs 102)
    state = tracker.update(current_price=101.0, current_atr=1.0)
    assert not state["is_active"]
    assert state["stop_price"] is None
    assert not state["stop_hit"]

    # Price rises to 105 -> activated! Peak = 105, ATR = 1.5 -> Stop = 105 - (2*1.5) = 102.0
    state = tracker.update(current_price=105.0, current_atr=1.5)
    assert state["is_active"]
    assert state["stop_price"] == 102.0
    assert not state["stop_hit"]

    # Price rises to 110 -> Peak = 110, ATR = 1.5 -> Stop moves up to 107.0
    state = tracker.update(current_price=110.0, current_atr=1.5)
    assert state["stop_price"] == 107.0

    # Price drops to 108 -> Stop remains locked at 107.0
    state = tracker.update(current_price=108.0, current_atr=1.5)
    assert state["stop_price"] == 107.0
    assert not state["stop_hit"]

    # Price drops to 106.5 (below 107.0) -> Stop hit!
    state = tracker.update(current_price=106.5, current_atr=1.5)
    assert state["stop_hit"]


def test_short_trailing_stop():
    # Short @ $100, activation at +2% ($98.0)
    tracker = DynamicTrailingStop(
        symbol="ETHUSDT",
        side="SHORT",
        entry_price=100.0,
        activation_pct=0.02,
        atr_multiplier=1.0
    )

    # Price drops to 95.0 -> Activated. Stop = 95 + (1.0 * 2.0) = 97.0
    state = tracker.update(current_price=95.0, current_atr=2.0)
    assert state["is_active"]
    assert state["stop_price"] == 97.0
    assert not state["stop_hit"]

    # Price bounces to 97.5 -> Stop hit!
    state = tracker.update(current_price=97.5, current_atr=2.0)
    assert state["stop_hit"]
