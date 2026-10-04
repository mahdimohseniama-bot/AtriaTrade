import os
import pytest
from src.exchange.wallex_live_guard import WallexLiveGuard
from src.exchange.wallex_order_executor import WallexOrderExecutor

def test_stage16_live_guard_blocks_by_default():
    print("[STAGE 16] LIVE GUARD TEST STARTING...")

    os.environ.pop("ALLOW_WALLEX_LIVE", None)
    os.environ.pop("WALLEX_KILL_SWITCH", None)
    os.environ.pop("WALLEX_API_KEY", None)
    os.environ.pop("WALLEX_API_SECRET", None)

    guard = WallexLiveGuard()
    cfg = guard.read_config()

    assert cfg.allow_live is False
    assert cfg.kill_switch is False
    assert cfg.api_key_present is False
    assert cfg.api_secret_present is False

    ex = WallexOrderExecutor(dry_run=False)
    with pytest.raises(RuntimeError, match="LIVE_BLOCKED"):
        ex.place_limit_order("TMNUSDT", "BUY", price=100000.0, quantity=5.0)

    print("[SUCCESS] Stage 16 Default Live Block Passed!")

def test_stage16_kill_switch_blocks_live():
    print("[STAGE 16] KILL-SWITCH TEST STARTING...")

    os.environ["ALLOW_WALLEX_LIVE"] = "1"
    os.environ["WALLEX_API_KEY"] = "test_key"
    os.environ["WALLEX_API_SECRET"] = "test_secret"
    os.environ["WALLEX_KILL_SWITCH"] = "1"

    ex = WallexOrderExecutor(dry_run=False)

    try:
        ex.place_limit_order("TMNUSDT", "BUY", price=100000.0, quantity=5.0)
        assert False, "Expected RuntimeError due to kill-switch"
    except RuntimeError as e:
        assert "LIVE_BLOCKED" in str(e)

    print("[SUCCESS] Stage 16 Live Guard Kill-Switch Passed!")
