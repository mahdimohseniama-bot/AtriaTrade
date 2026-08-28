from typing import Dict, Any, List


class PortfolioRebalancer:
    """
    Analyzes current asset allocations versus target model weights and
    generates rebalancing orders when allocation drift exceeds defined thresholds.
    """
    def __init__(self, drift_threshold_pct: float = 0.05):
        """
        :param drift_threshold_pct: Minimum percentage deviation (e.g. 0.05 = 5%) required to trigger rebalance.
        """
        self.drift_threshold_pct = drift_threshold_pct

    def calculate_current_allocations(
        self,
        balances: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculates portfolio percentage allocation for each asset.
        """
        asset_values = {}
        total_value = 0.0

        for asset, amount in balances.items():
            if asset.upper() in ["USDT", "USD", "IRR", "USDC", "CASH"]:
                val = amount
            else:
                price = prices.get(asset, 0.0)
                val = amount * price

            asset_values[asset] = val
            total_value += val

        if total_value <= 0:
            return {asset: 0.0 for asset in balances}

        return {asset: val / total_value for asset, val in asset_values.items()}

    def generate_rebalance_orders(
        self,
        current_balances: Dict[str, float],
        current_prices: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Generates buy/sell actions to realign portfolio with target weights.
        """
        current_weights = self.calculate_current_allocations(current_balances, current_prices)
        
        # Calculate total portfolio USD value
        total_value = 0.0
        for asset, amount in current_balances.items():
            if asset.upper() in ["USDT", "USD", "IRR", "USDC", "CASH"]:
                total_value += amount
            else:
                price = current_prices.get(asset, 0.0)
                total_value += amount * price

        if total_value <= 0:
            return []

        orders = []
        for asset, target_weight in target_weights.items():
            current_weight = current_weights.get(asset, 0.0)
            drift = target_weight - current_weight

            if abs(drift) >= self.drift_threshold_pct:
                target_value = total_value * target_weight
                current_asset_val = (
                    current_balances.get(asset, 0.0)
                    if asset.upper() in ["USDT", "USD", "IRR", "USDC", "CASH"]
                    else current_balances.get(asset, 0.0) * current_prices.get(asset, 0.0)
                )
                delta_value = target_value - current_asset_val
                
                price = current_prices.get(asset, 1.0)
                if price <= 0:
                    continue

                order_amount = abs(delta_value) / price
                side = "BUY" if delta_value > 0 else "SELL"

                orders.append({
                    "asset": asset,
                    "side": side,
                    "amount": round(order_amount, 6),
                    "value_usd": round(abs(delta_value), 2),
                    "current_weight": round(current_weight, 4),
                    "target_weight": round(target_weight, 4),
                    "drift_pct": round(drift * 100, 2)
                })

        return orders
