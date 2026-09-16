import math
from typing import List, Dict, Any, Optional, Tuple


class CorrelationManager:
    """
    Calculates multi-asset correlation matrices and prevents concentrated
    risk exposure across highly correlated trading pairs.
    """
    def __init__(self, max_allowed_correlation: float = 0.80):
        self.max_allowed_correlation = max_allowed_correlation

    def calculate_pearson_correlation(
        self,
        series_a: List[float],
        series_b: List[float]
    ) -> float:
        """
        Calculates Pearson correlation coefficient between two price or return series.
        Returns value in range [-1.0, 1.0].
        """
        n = min(len(series_a), len(series_b))
        if n < 2:
            return 0.0

        x = series_a[-n:]
        y = series_b[-n:]

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        diff_x = [val - mean_x for val in x]
        diff_y = [val - mean_y for val in y]

        sum_prod_diff = sum(dx * dy for dx, dy in zip(diff_x, diff_y))
        sum_sq_diff_x = sum(dx ** 2 for dx in diff_x)
        sum_sq_diff_y = sum(dy ** 2 for dy in diff_y)

        denominator = math.sqrt(sum_sq_diff_x * sum_sq_diff_y)
        if denominator == 0:
            return 0.0

        corr = sum_prod_diff / denominator
        return max(-1.0, min(1.0, corr))

    def evaluate_new_trade_risk(
        self,
        new_symbol: str,
        new_side: str,
        active_positions: Dict[str, Dict[str, Any]],
        price_history: Dict[str, List[float]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether opening a new position exceeds correlation thresholds
        with currently active positions.
        """
        if not active_positions:
            return True, None

        if new_symbol not in price_history:
            return True, None

        new_series = price_history[new_symbol]
        normalized_new_side = new_side.upper()

        for open_symbol, pos_data in active_positions.items():
            if open_symbol == new_symbol:
                continue

            if open_symbol not in price_history:
                continue

            open_side = pos_data.get("side", "LONG").upper()
            open_series = price_history[open_symbol]

            corr = self.calculate_pearson_correlation(new_series, open_series)

            # If both are same direction (e.g. LONG & LONG) and highly positively correlated
            if (open_side == normalized_new_side) and (corr >= self.max_allowed_correlation):
                return False, f"High positive correlation ({corr:.2f}) with active {open_symbol} position."

            # If opposite directions and highly negatively correlated (effectively same directional bet)
            if (open_side != normalized_new_side) and (corr <= -self.max_allowed_correlation):
                return False, f"High inverse correlation ({corr:.2f}) amplifying exposure against {open_symbol}."

        return True, None
