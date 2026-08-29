from typing import Dict, List, Any

class StrategyOrchestrator:
    """
    ارکستراتور استراتژی‌ها: سیگنال‌های چند استراتژی را با وزن و اعتماد
    دریافت کرده و با قاعده اجماع وزنی، تصمیم نهایی صادر می‌کند.
    """
    def __init__(self, strategy_weights: Dict[str, float], min_confidence: float = 0.6, min_score: float = 0.3):
        if not strategy_weights:
            raise ValueError("strategy_weights cannot be empty.")
        if any(w <= 0 for w in strategy_weights.values()):
            raise ValueError("All strategy weights must be positive.")
        self.strategy_weights = dict(strategy_weights)
        self.min_confidence = min_confidence
        self.min_score = min_score

    def _validate_signal(self, signal: Dict[str, Any]) -> None:
        strategy = signal.get("strategy")
        if strategy not in self.strategy_weights:
            raise ValueError(f"Unknown strategy: {strategy}")
        if signal.get("action") not in ("BUY", "SELL"):
            raise ValueError(f"Invalid action: {signal.get('action')}")
        conf = float(signal.get("confidence", 0.0))
        if not (0.0 <= conf <= 1.0):
            raise ValueError("Confidence must be between 0 and 1.")

    def decide(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        signals: لیستی از {'strategy': 'smc', 'action': 'BUY', 'confidence': 0.8}
        خروجی: {'decision': 'BUY'|'SELL'|'HOLD', 'score': float, 'detail': dict}
        """
        buy_score = 0.0
        sell_score = 0.0
        contributing = []

        for sig in signals:
            self._validate_signal(sig)
            conf = float(sig.get("confidence", 0.0))
            if conf < self.min_confidence:
                # سیگنال کم‌اعتماد در تصمیم مشارکت نمی‌کند
                continue
            weight = self.strategy_weights[sig["strategy"]]
            score = weight * conf
            if sig["action"] == "BUY":
                buy_score += score
            else:
                sell_score += score
            contributing.append(sig)

        net_score = round(buy_score - sell_score, 4)
        if net_score >= self.min_score:
            decision = "BUY"
        elif net_score <= -self.min_score:
            decision = "SELL"
        else:
            decision = "HOLD"

        return {
            "decision": decision,
            "score": net_score,
            "buy_score": round(buy_score, 4),
            "sell_score": round(sell_score, 4),
            "contributing_signals": contributing,
            "thresholds": {"min_confidence": self.min_confidence, "min_score": self.min_score},
        }
