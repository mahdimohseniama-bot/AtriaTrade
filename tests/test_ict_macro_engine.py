"""
Unit tests for ICT Macro & Time-Window Liquidity Engine (Capability 95)
"""

from datetime import time
import pytest
from src.core.ict_macro_engine import ICTMacroEngine, WindowType


def test_no_active_window_outside_hours():
    engine = ICTMacroEngine()
    # 06:15 NY time (No active killzone or macro)
    t = time(6, 15)
    active = engine.get_active_windows(t)
    assert len(active) == 0
    assert engine.evaluate_timing_factor(t) == 1.0
    assert engine.is_macro_active(t) is False


def test_killzone_activation():
    engine = ICTMacroEngine()
    # 02:15 NY time (Inside London Open Killzone, but outside 02:33 Macro)
    t = time(2, 15)
    active = engine.get_active_windows(t)
    assert len(active) == 1
    assert active[0].name == "London Open Killzone"
    assert active[0].window_type == WindowType.KILLZONE
    assert engine.evaluate_timing_factor(t) == 1.5
    assert engine.is_macro_active(t) is False


def test_macro_overlapping_killzone_max_boost():
    engine = ICTMacroEngine()
    # 09:55 NY time (Inside NY Open Killzone AND inside NY AM 09:50 Macro)
    t = time(9, 55)
    active = engine.get_active_windows(t)
    assert len(active) == 2
    assert engine.is_macro_active(t) is True
    # Boost should take the max (Macro 2.0 > Killzone 1.6)
    assert engine.evaluate_timing_factor(t) == 2.0


def test_midnight_wrap_around_asian_killzone():
    engine = ICTMacroEngine()
    # 22:30 NY time (Inside Asian Killzone 20:00 - 00:00)
    t = time(22, 30)
    active = engine.get_active_windows(t)
    assert any(win.name == "Asian Killzone" for win in active)
    assert engine.evaluate_timing_factor(t) == 1.2
