import pytest
from src.core.walk_forward import WalkForwardValidator, WindowSplit

def test_walk_forward_split_generation():
    validator = WalkForwardValidator(train_size=100, test_size=20, step_size=20)
    splits = validator.generate_splits(total_records=160)
    
    assert len(splits) == 3
    assert splits[0] == WindowSplit(train_start=0, train_end=100, test_start=100, test_end=120)
    assert splits[1] == WindowSplit(train_start=20, train_end=120, test_start=120, test_end=140)
    assert splits[2] == WindowSplit(train_start=40, train_end=140, test_start=140, test_end=160)

def test_walk_forward_data_slices():
    data = [{"close": i} for i in range(200)]
    validator = WalkForwardValidator(train_size=80, test_size=20)
    slices = validator.split_data(data)
    
    assert len(slices) > 0
    train_0, test_0 = slices[0]
    assert len(train_0) == 80
    assert len(test_0) == 20
    assert train_0[-1]["close"] == 79
    assert test_0[0]["close"] == 80

def test_walk_forward_insufficient_data():
    validator = WalkForwardValidator(train_size=100, test_size=50)
    splits = validator.generate_splits(total_records=120)
    assert splits == []

def test_invalid_parameters():
    with pytest.raises(ValueError):
        WalkForwardValidator(train_size=0, test_size=10)
    with pytest.raises(ValueError):
        WalkForwardValidator(train_size=50, test_size=-5)
    with pytest.raises(ValueError):
        WalkForwardValidator(train_size=50, test_size=10, step_size=0)

def test_walk_forward_efficiency_calculation():
    validator = WalkForwardValidator(train_size=100, test_size=20)
    # 10% OOS vs 15% IS -> WFE = ~0.666
    wfe = validator.calculate_walk_forward_efficiency(0.15, 0.10)
    assert round(wfe, 3) == 0.667

    # Zero IS returns handled gracefully
    assert validator.calculate_walk_forward_efficiency(0.0, 0.05) == 1.0
    assert validator.calculate_walk_forward_efficiency(0.0, -0.05) == 0.0
