import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

@dataclass
class StrategyConfig:
    strategy_name: str
    version: str = "1.0.0"
    timeframe: str = "1h"
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        if not self.strategy_name or not isinstance(self.strategy_name, str):
            raise ValueError("strategy_name must be a non-empty string")
        if not self.version or not isinstance(self.version, str):
            raise ValueError("version must be a non-empty string")
        self._validate_parameters()

    def _validate_parameters(self):
        # Specific sanity validations if parameters present
        if "rsi_period" in self.parameters:
            p = self.parameters["rsi_period"]
            if not isinstance(p, int) or p <= 1 or p > 100:
                raise ValueError("rsi_period must be an integer between 2 and 100")
                
        if "fast_ema" in self.parameters and "slow_ema" in self.parameters:
            f = self.parameters["fast_ema"]
            s = self.parameters["slow_ema"]
            if not (isinstance(f, int) and isinstance(s, int)):
                raise ValueError("EMA periods must be integers")
            if f >= s:
                raise ValueError("fast_ema must be strictly less than slow_ema")

    def get_hash(self) -> str:
        """
        Generates deterministic SHA-256 hash of configuration payload.
        """
        payload = {
            "strategy_name": self.strategy_name,
            "version": self.version,
            "timeframe": self.timeframe,
            "parameters": self.parameters,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["config_hash"] = self.get_hash()
        return d

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyConfig":
        clean_data = data.copy()
        clean_data.pop("config_hash", None)
        return cls(**clean_data)

    @classmethod
    def from_json(cls, json_str: str) -> "StrategyConfig":
        data = json.loads(json_str)
        return cls.from_dict(data)
