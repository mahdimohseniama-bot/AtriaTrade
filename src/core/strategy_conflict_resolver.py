from typing import List, Dict, Any, Optional


class StrategyConflictResolver:
    """
    Resolves contradictory signals across multiple strategies on the same symbol.
    Uses confidence-weighted scores and net consensus thresholds.
    """
    def __init__(self, min_net_score: float = 0.20, disagreement_tolerance: float = 0.35):
        """
        :param min_net_score: Minimum net score (Buy - Sell) required to approve an action.
        :param disagreement_tolerance: Max allowed opposite signal weight ratio before flagging hard conflict.
        """
        if min_net_score < 0:
            raise ValueError("min_net_score cannot be negative.")
        if not (0.0 <= disagreement_tolerance <= 1.0):
            raise ValueError("disagreement_tolerance must be between 0.0 and 1.0.")
            
        self.min_net_score = min_net_score
        self.disagreement_tolerance = disagreement_tolerance

    def resolve(self, symbol: str, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a list of strategy signals for a symbol.
        Each signal dict: {
            'strategy_name': str,
            'direction': 'BUY' | 'SELL' | 'HOLD',
            'confidence': float (0.0 to 1.0),
            'weight': float (default 1.0)
        }
        Returns resolved decision dict.
        """
        if not signals:
            return {
                "symbol": symbol,
                "action": "HOLD",
                "net_score": 0.0,
                "has_conflict": False,
                "reason": "No signals provided."
            }

        buy_weight = 0.0
        sell_weight = 0.0
        total_weight = 0.0

        for sig in signals:
            direction = sig.get("direction", "HOLD").upper()
            conf = float(sig.get("confidence", 0.5))
            w = float(sig.get("weight", 1.0))
            score = conf * w

            if direction == "BUY":
                buy_weight += score
                total_weight += w
            elif direction == "SELL":
                sell_weight += score
                total_weight += w
            elif direction == "HOLD":
                total_weight += w
            else:
                raise ValueError(f"Unknown direction: {direction}")

        if total_weight == 0.0:
            return {
                "symbol": symbol,
                "action": "HOLD",
                "net_score": 0.0,
                "has_conflict": False,
                "reason": "Total strategy weight is zero."
            }

        normalized_buy = buy_weight / total_weight
        normalized_sell = sell_weight / total_weight
        net_score = normalized_buy - normalized_sell

        # Check for hard conflict (both Buy and Sell have notable strength)
        min_opposing = min(normalized_buy, normalized_sell)
        max_opposing = max(normalized_buy, normalized_sell)
        has_conflict = False

        if min_opposing > 0 and (min_opposing / (max_opposing + 1e-9)) > self.disagreement_tolerance:
            has_conflict = True

        if has_conflict:
            return {
                "symbol": symbol,
                "action": "HOLD",
                "net_score": round(net_score, 4),
                "has_conflict": True,
                "reason": f"Severe strategy conflict: BUY={round(normalized_buy, 3)}, SELL={round(normalized_sell, 3)}"
            }

        if net_score >= self.min_net_score:
            action = "BUY"
            reason = "Buy consensus threshold reached."
        elif net_score <= -self.min_net_score:
            action = "SELL"
            reason = "Sell consensus threshold reached."
        else:
            action = "HOLD"
            reason = f"Net score {round(net_score, 4)} below threshold {self.min_net_score}."

        return {
            "symbol": symbol,
            "action": action,
            "net_score": round(net_score, 4),
            "has_conflict": False,
            "reason": reason
        }
