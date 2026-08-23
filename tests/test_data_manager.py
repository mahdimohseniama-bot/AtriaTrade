"""
Tests for DataManager
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.data_manager import DataManager

def test_data_manager():
    print("=" * 55)
    print("START: Data Manager Tests")
    print("=" * 55)

    dm = DataManager(base_path="data/test_storage")
    
    sample_data = [
        {"timestamp": 1625097600000, "open": 35000.0, "high": 35500.0, "low": 34800.0, "close": 35200.0, "volume": 100.5},
        {"timestamp": 1625097660000, "open": 35200.0, "high": 35800.0, "low": 35100.0, "close": 35700.0, "volume": 150.2}
    ]

    # Test Saving
    path = dm.save_to_csv("BTCUSDT", sample_data)
    assert os.path.exists(path)
    print(f"[OK] Data saved to {path}")

    # Test Loading
    loaded_data = dm.load_from_csv("BTCUSDT")
    assert len(loaded_data) == 2
    assert loaded_data[0]['close'] == 35200.0
    assert isinstance(loaded_data[0]['timestamp'], int)
    print("[OK] Data loaded and validated")

    # Clean up test data
    os.remove(path)
    os.rmdir("data/test_storage")
    
    print("=" * 55)
    print("=== DATA MANAGER TEST PASSED ===")

if __name__ == "__main__":
    test_data_manager()
