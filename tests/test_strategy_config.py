import pytest
from src.core.strategy_config import StrategyConfig

def test_valid_strategy_config_creation():
    cfg = StrategyConfig(
        strategy_name="EMA_Cross_RSI",
        version="1.2.0",
        timeframe="15m",
        parameters={"fast_ema": 9, "slow_ema": 21, "rsi_period": 14},
        description="Standard trend following strategy"
    )
    assert cfg.strategy_name == "EMA_Cross_RSI"
    assert cfg.version == "1.2.0"
    assert len(cfg.get_hash()) == 64

def test_hash_determinism_and_uniqueness():
    cfg1 = StrategyConfig(
        strategy_name="TrendFlow",
        parameters={"fast_ema": 10, "slow_ema": 50}
    )
    cfg2 = StrategyConfig(
        strategy_name="TrendFlow",
        parameters={"fast_ema": 10, "slow_ema": 50}
    )
    cfg3 = StrategyConfig(
        strategy_name="TrendFlow",
        parameters={"fast_ema": 12, "slow_ema": 50}
    )

    assert cfg1.get_hash() == cfg2.get_hash()
    assert cfg1.get_hash() != cfg3.get_hash()

def test_serialization_and_deserialization():
    cfg = StrategyConfig(
        strategy_name="Scalper",
        version="2.0.0",
        parameters={"rsi_period": 14}
    )
    json_str = cfg.to_json()
    loaded_cfg = StrategyConfig.from_json(json_str)

    assert loaded_cfg.strategy_name == cfg.strategy_name
    assert loaded_cfg.version == cfg.version
    assert loaded_cfg.get_hash() == cfg.get_hash()

def test_invalid_parameters_validation():
    with pytest.raises(ValueError):
        StrategyConfig(strategy_name="", version="1.0.0")

    with pytest.raises(ValueError):
        StrategyConfig(strategy_name="RSI_Bot", parameters={"rsi_period": 150})

    with pytest.raises(ValueError):
        # fast_ema >= slow_ema is invalid
        StrategyConfig(strategy_name="EMA_Bot", parameters={"fast_ema": 50, "slow_ema": 20})
