import os
import pytest
from src.core.monitoring import AtriaLogger

def test_logger_creates_file():
    log_path = "logs/test_atria.log"
    if os.path.exists(log_path):
        os.remove(log_path)
        
    atria_log = AtriaLogger(name="TestLogger", log_file=log_path).get_logger()
    atria_log.info("Test log message for verification")
    
    assert os.path.exists(log_path)
    with open(log_path, "r") as f:
        content = f.read()
        assert "Test log message for verification" in content
        assert "[INFO]" in content
