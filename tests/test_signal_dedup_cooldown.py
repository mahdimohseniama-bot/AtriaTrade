import pytest
from src.core.signal_dedup_cooldown import SignalDedupCooldownManager


def test_first_entry_allowed():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    assert mgr.is_duplicate("BTCUSDT", "BUY", now=1000.0) is False


def test_duplicate_within_cooldown_blocked():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    mgr.register_entry("BTCUSDT", "BUY", now=1000.0)
    # ۳۰۰ ثانیه بعد => هنوز در Cooldown
    assert mgr.is_duplicate("BTCUSDT", "BUY", now=1300.0) is True


def test_entry_allowed_after_cooldown_expires():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    mgr.register_entry("BTCUSDT", "BUY", now=1000.0)
    # ۶۰۱ ثانیه بعد => آزاد
    assert mgr.is_duplicate("BTCUSDT", "BUY", now=1601.0) is False


def test_opposite_direction_independent():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    mgr.register_entry("BTCUSDT", "BUY", now=1000.0)
    # جهت مخالف تحت تأثیر Cooldown خرید نیست
    assert mgr.is_duplicate("BTCUSDT", "SELL", now=1100.0) is False


def test_remaining_cooldown_calculation():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    mgr.register_entry("ETHUSDT", "SELL", now=2000.0)
    assert mgr.remaining_cooldown("ETHUSDT", "SELL", now=2300.0) == 300.0
    assert mgr.remaining_cooldown("ETHUSDT", "SELL", now=3000.0) == 0.0


def test_clear_entry_resets_state():
    mgr = SignalDedupCooldownManager(cooldown_seconds=600)
    mgr.register_entry("BTCUSDT", "BUY", now=1000.0)
    mgr.clear_entry("BTCUSDT", "BUY")
    assert mgr.is_duplicate("BTCUSDT", "BUY", now=1001.0) is False


def test_invalid_direction_rejected():
    mgr = SignalDedupCooldownManager()
    with pytest.raises(ValueError):
        mgr.is_duplicate("BTCUSDT", "HOLD", now=1000.0)


def test_negative_cooldown_rejected():
    with pytest.raises(ValueError):
        SignalDedupCooldownManager(cooldown_seconds=-1)
