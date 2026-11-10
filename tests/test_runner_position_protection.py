import pytest
from unittest.mock import MagicMock
from src.core.position_protector import DynamicPositionProtector

def test_runner_tp_sl_logic():
    protector = DynamicPositionProtector(sl_pct=0.01, tp_pct=0.02)
    entry_price = 100.0
    levels = protector.calculate_levels(entry_price, "LONG")
    
    assert levels["sl_price"] == 99.0
    assert levels["tp_price"] == 102.0
    
    # Test SL trigger
    assert protector.check_exit("LONG", 98.9, levels) == "SL_TRIGGERED"
    
    # Test TP trigger
    assert protector.check_exit("LONG", 102.1, levels) == "TP_TRIGGERED"
    
    # Inside bounds
    assert protector.check_exit("LONG", 100.5, levels) is None
