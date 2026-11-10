import pytest
from src.core.position_protector import DynamicPositionProtector

def test_long_protection_levels():
    protector = DynamicPositionProtector(sl_pct=0.02, tp_pct=0.04)
    levels = protector.calculate_levels(entry_price=100.0, side="LONG")
    
    assert levels["sl_price"] == 98.0
    assert levels["tp_price"] == 104.0
    
    # Check SL trigger
    assert protector.check_exit("LONG", 97.5, levels) == "SL_TRIGGERED"
    # Check TP trigger
    assert protector.check_exit("LONG", 104.5, levels) == "TP_TRIGGERED"
    # Inside bounds
    assert protector.check_exit("LONG", 100.0, levels) is None

def test_short_protection_levels():
    protector = DynamicPositionProtector(sl_pct=0.02, tp_pct=0.04)
    levels = protector.calculate_levels(entry_price=100.0, side="SHORT")
    
    assert levels["sl_price"] == 102.0
    assert levels["tp_price"] == 96.0
    
    # Check SL trigger
    assert protector.check_exit("SHORT", 102.5, levels) == "SL_TRIGGERED"
    # Check TP trigger
    assert protector.check_exit("SHORT", 95.5, levels) == "TP_TRIGGERED"
    # Inside bounds
    assert protector.check_exit("SHORT", 100.0, levels) is None
