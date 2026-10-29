import os
from src.exchange.wallex_env_verifier import WallexEnvVerifier

def test_stage21_default_safe_state(monkeypatch):
    monkeypatch.delenv("WALLEX_API_KEY", raising=False)
    monkeypatch.delenv("ATRIA_LIVE_MODE", raising=False)
    monkeypatch.delenv("ATRIA_KILL_SWITCH", raising=False)
    
    status = WallexEnvVerifier.verify()
    assert status["live_mode_enabled"] is False
    assert status["kill_switch_active"] is False
    assert status["execution_ready"] is True
    assert status["mode_label"] == "DRY_RUN"

def test_stage21_kill_switch_blocks(monkeypatch):
    monkeypatch.setenv("ATRIA_KILL_SWITCH", "1")
    monkeypatch.setenv("ATRIA_LIVE_MODE", "1")
    monkeypatch.setenv("WALLEX_API_KEY", "wallex-token-1234567890")
    
    status = WallexEnvVerifier.verify()
    assert status["kill_switch_active"] is True
    assert status["execution_ready"] is False
    assert status["mode_label"] == "DRY_RUN"

def test_stage21_live_mode_ready(monkeypatch):
    monkeypatch.setenv("ATRIA_KILL_SWITCH", "0")
    monkeypatch.setenv("ATRIA_LIVE_MODE", "1")
    monkeypatch.setenv("WALLEX_API_KEY", "wallex-token-valid-string-123")
    
    status = WallexEnvVerifier.verify()
    assert status["live_mode_enabled"] is True
    assert status["execution_ready"] is True
    assert status["mode_label"] == "LIVE"
