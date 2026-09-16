from typing import Dict, Any, Tuple


class DynamicSpreadFeeFilter:
    """
    Evaluates whether an intended trade has sufficient expected profit margin 
    relative to current bid-ask spread and round-trip exchange fees.
    """
    def __init__(
        self, 
        max_spread_pct: float = 0.005,         # 0.5% max allowed spread
        default_taker_fee: float = 0.001,      # 0.1% per leg (0.2% round-trip)
        min_reward_to_cost_ratio: float = 2.0  # Target profit must be >= 2x friction cost
    ):
        if max_spread_pct <= 0:
            raise ValueError("max_spread_pct must be positive.")
        if default_taker_fee < 0:
            raise ValueError("default_taker_fee cannot be negative.")
        if min_reward_to_cost_ratio <= 0:
            raise ValueError("min_reward_to_cost_ratio must be positive.")

        self.max_spread_pct = max_spread_pct
        self.default_taker_fee = default_taker_fee
        self.min_reward_to_cost_ratio = min_reward_to_cost_ratio

    def evaluate_order(
        self, 
        best_bid: float, 
        best_ask: float, 
        target_exit_price: float, 
        side: str = "BUY",
        custom_fee_rate: float = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Calculates spread and total friction costs, checking if trade is viable.
        Returns: (is_approved: bool, reason: str, metrics: dict)
        """
        if best_bid <= 0 or best_ask <= 0 or target_exit_price <= 0:
            return False, "Invalid price inputs (must be positive).", {}
        if best_ask < best_bid:
            return False, f"Inverted orderbook: ask ({best_ask}) < bid ({best_bid}).", {}

        side = side.upper()
        if side not in ["BUY", "SELL"]:
            return False, f"Invalid trade side: {side}", {}

        mid_price = (best_bid + best_ask) / 2.0
        spread_abs = best_ask - best_bid
        spread_pct = spread_abs / mid_price

        # Check maximum spread anomaly
        if spread_pct > self.max_spread_pct:
            return False, f"Spread {spread_pct:.4%} exceeds max limit {self.max_spread_pct:.4%}.", {
                "spread_pct": spread_pct,
                "mid_price": mid_price
            }

        fee_rate = self.default_taker_fee if custom_fee_rate is None else custom_fee_rate
        round_trip_fee_pct = 2.0 * fee_rate
        total_friction_pct = spread_pct + round_trip_fee_pct

        # Calculate expected gross return
        if side == "BUY":
            # Entering at ask, exiting at target
            entry_price = best_ask
            gross_return_pct = (target_exit_price - entry_price) / entry_price
        else:
            # Entering at bid, exiting at target
            entry_price = best_bid
            gross_return_pct = (entry_price - target_exit_price) / entry_price

        if gross_return_pct <= 0:
            return False, f"Target exit price yields non-positive gross return ({gross_return_pct:.4%}).", {
                "gross_return_pct": gross_return_pct,
                "total_friction_pct": total_friction_pct
            }

        net_return_pct = gross_return_pct - total_friction_pct
        reward_to_cost = gross_return_pct / (total_friction_pct + 1e-9)

        metrics = {
            "entry_price": entry_price,
            "spread_pct": round(spread_pct, 6),
            "round_trip_fee_pct": round(round_trip_fee_pct, 6),
            "total_friction_pct": round(total_friction_pct, 6),
            "gross_return_pct": round(gross_return_pct, 6),
            "net_return_pct": round(net_return_pct, 6),
            "reward_to_cost_ratio": round(reward_to_cost, 2)
        }

        if reward_to_cost < self.min_reward_to_cost_ratio:
            return False, f"Reward-to-cost ratio {reward_to_cost:.2f} below required {self.min_reward_to_cost_ratio:.2f}.", metrics

        return True, "Trade approved by spread and fee filter.", metrics
