from src.core.position_tracker import PositionTracker


def test_position_lifecycle():
    print("[1] Initializing PositionTracker...")
    tracker = PositionTracker()

    print("[2] Opening Long position for BTCUSDT with SL and TP...")
    pos = tracker.open_position(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=50000.0,
        size=0.1,
        sl=49000.0,
        tp=53000.0,
    )
    assert pos["symbol"] == "BTCUSDT"
    assert tracker.get_position("BTCUSDT") is not None
    print("-> Position opened successfully.")

    print("[3] Testing SL / TP triggers...")
    assert tracker.check_sl_tp("BTCUSDT", 51000.0) is None
    assert tracker.check_sl_tp("BTCUSDT", 48900.0) == "SL"
    assert tracker.check_sl_tp("BTCUSDT", 53500.0) == "TP"
    print("-> SL/TP logic validated.")

    print("[4] Closing position...")
    closed_pos = tracker.close_position("BTCUSDT", exit_price=52000.0)
    assert closed_pos["exit_price"] == 52000.0
    assert tracker.get_position("BTCUSDT") is None
    print("-> Position closed successfully.")

    print("=== POSITION TRACKER TEST PASSED ===")


if __name__ == "__main__":
    test_position_lifecycle()
