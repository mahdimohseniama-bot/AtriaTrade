"""
Dynamic Spread and Fee Filter for AtriaTrade.
All logs and outputs strictly in English.
"""

from typing import Tuple, Dict, Any, Optional

class DynamicSpreadFeeFilter:
    def __init__(
        self,
        max_spread_pct: float = 0.005,
        default_taker_fee: float = 0.001,
        min_reward_to_cost_ratio: float = 2.0,
        **kwargs
    ):
        if max_spread_pct <= 0 or min_reward_to_cost_ratio <= 0:
            raise ValueError("Parameters max_spread_pct and min_reward_to_cost_ratio must be positive.")
        if default_taker_fee < 0:
            raise ValueError("default_taker_fee cannot be negative.")

        self.max_spread_pct = float(max_spread_pct)
        fee_val = kwargs.get("taker_fee_pct", default_taker_fee)
        self.default_taker_fee = float(fee_val)
        self.taker_fee_pct = self.default_taker_fee
        self.min_reward_to_cost_ratio = float(min_reward_to_cost_ratio)

    def evaluate_spread(self, best_bid: float, best_ask: float) -> Dict[str, Any]:
        best_bid = float(best_bid)
        best_ask = float(best_ask)
        if best_bid <= 0 or best_ask <= 0:
            return {"allowed": False, "reason": "INVALID_PRICES", "spread_pct": 0.0, "est_roundtrip_cost_pct": 0.0}
        if best_ask < best_bid:
            return {"allowed": False, "reason": "INVERTED_ORDERBOOK", "spread_pct": 0.0, "est_roundtrip_cost_pct": 0.0}

        spread_pct = round(((best_ask - best_bid) / best_bid) * 100.0, 4)
        threshold = self.max_spread_pct if self.max_spread_pct > 0.05 else self.max_spread_pct * 100.0
        allowed = spread_pct <= threshold

        return {
            "allowed": allowed,
            "reason": "OK" if allowed else "SPREAD_TOO_HIGH",
            "spread_pct": spread_pct,
            "est_roundtrip_cost_pct": spread_pct + (self.default_taker_fee * 2.0 * 100.0)
        }

    def evaluate_order(
        self,
        best_bid: float,
        best_ask: float,
        target_exit_price: float,
        side: str = "BUY",
        custom_fee_rate: Optional[float] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        best_bid = float(best_bid)
        best_ask = float(best_ask)
        target_exit_price = float(target_exit_price)
        side_norm = str(side).upper()

        if best_bid <= 0 or best_ask <= 0 or target_exit_price <= 0:
            return False, "Invalid prices provided", {}
        if best_ask < best_bid:
            return False, "Inverted orderbook detected", {}
        if side_norm not in ("BUY", "SELL"):
            return False, f"Unsupported side: {side}", {}

        mid_price = (best_bid + best_ask) / 2.0
        spread_pct = (best_ask - best_bid) / best_bid
        threshold = self.max_spread_pct if self.max_spread_pct <= 0.05 else self.max_spread_pct / 100.0

        if spread_pct > threshold:
            reason = "Spread exceeds maximum threshold (SPREAD_TOO_HIGH)"
            return False, reason, {"spread_pct": spread_pct * 100.0, "mid_price": mid_price}

        fee_rate = float(custom_fee_rate) if custom_fee_rate is not None else self.default_taker_fee
        round_trip_fee_pct = fee_rate * 2.0
        total_friction_pct = spread_pct + round_trip_fee_pct

        if side_norm == "BUY":
            entry_price = best_ask
            gross_return_pct = (target_exit_price - entry_price) / entry_price
        else:
            entry_price = best_bid
            gross_return_pct = (entry_price - target_exit_price) / entry_price

        if gross_return_pct <= 0:
            return False, "Target exit price yields non-positive gross return", {
                "gross_return_pct": gross_return_pct * 100.0,
                "total_friction_pct": total_friction_pct * 100.0
            }

        net_return_pct = gross_return_pct - total_friction_pct
        reward_to_cost_ratio = gross_return_pct / total_friction_pct if total_friction_pct > 0 else 0.0

        metrics = {
            "entry_price": entry_price,
            "spread_pct": spread_pct * 100.0,
            "round_trip_fee_pct": round_trip_fee_pct * 100.0,
            "total_friction_pct": total_friction_pct * 100.0,
            "gross_return_pct": gross_return_pct * 100.0,
            "net_return_pct": net_return_pct * 100.0,
            "reward_to_cost_ratio": reward_to_cost_ratio
        }

        if reward_to_cost_ratio < self.min_reward_to_cost_ratio:
            return False, f"Reward-to-cost ratio {reward_to_cost_ratio:.2f} below required {self.min_reward_to_cost_ratio:.2f}", metrics

        return True, "Trade approved by spread and fee filter.", metrics

SpreadFeeFilter = DynamicSpreadFeeFilter
