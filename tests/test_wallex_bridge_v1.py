import pytest
import os
from src.core import WallexOrderExecutor

def test_bridge_initialization():
    executor = WallexOrderExecutor(dry_run=True)
    assert executor.dry_run is True

def test_bridge_dry_run_execution():
    executor = WallexOrderExecutor(dry_run=True)
    response = executor.place_limit_order("BTCUSDT", "BUY", 90000, 0.01)
    assert response["status"] == "success"
    assert response["mode"] == "dry_run"
    assert response["filled_quantity"] == 0.01

def test_bridge_live_killswitch(monkeypatch):
    # ایزوله‌سازی کامل محیط برای تست
    monkeypatch.setenv("ALLOW_WALLEX_LIVE", "0")
    monkeypatch.delenv("WALLEX_API_KEY", raising=False)
    monkeypatch.delenv("WALLEX_API_SECRET", raising=False)
    
    executor = WallexOrderExecutor(dry_run=False)
    with pytest.raises(RuntimeError, match="LIVE_BLOCKED"):
        executor.place_limit_order("BTCUSDT", "BUY", 90000, 0.01)

def test_bridge_kill_switch_blocks_dry_run(monkeypatch):
    monkeypatch.setenv("WALLEX_KILL_SWITCH", "1")
    executor = WallexOrderExecutor(dry_run=True)
    with pytest.raises(RuntimeError, match="LIVE_BLOCKED"):
        executor.place_limit_order("BTCUSDT", "BUY", 90000, 0.01)
    monkeypatch.delenv("WALLEX_KILL_SWITCH", raising=False)

def test_bridge_dry_run_rejects_invalid_side():
    executor = WallexOrderExecutor(dry_run=True)
    with pytest.raises(ValueError):
        executor.place_limit_order("BTCUSDT", "HOLD", 90000, 0.01)
