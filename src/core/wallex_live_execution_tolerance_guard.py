from typing import Dict, Any, Optional

class WallexLiveExecutionToleranceGuard:
    """
    Guards live trade execution against adverse price drift and latency gaps
    between signal generation and actual order submission.
    """
    def __init__(self, max_price_drift_pct: float = 0.003, max_signal_age_sec: float = 10.0):
        self.max_price_drift_pct = max_price_drift_pct
        self.max_signal_age_sec = max_signal_age_sec

    def validate_execution_price(
        self,
        side: str,
        signal_price: float,
        current_market_price: float,
        signal_timestamp: float,
        current_timestamp: float
    ) -> Dict[str, Any]:
        age = current_timestamp - signal_timestamp
        if age > self.max_signal_age_sec:
            return {
                "allowed": False,
                "reason": "SIGNAL_EXPIRED",
                "age_sec": round(age, 2),
                "max_age_sec": self.max_signal_age_sec
            }

        if signal_price <= 0 or current_market_price <= 0:
            return {
                "allowed": False,
                "reason": "INVALID_PRICE_VALUES",
                "signal_price": signal_price,
                "current_price": current_market_price
            }

        normalized_side = side.upper()
        if normalized_side == "BUY":
            # For buy, drift is adverse if current market price is higher than signal
            drift_pct = (current_market_price - signal_price) / signal_price
        elif normalized_side == "SELL":
            # For sell, drift is adverse if current market price is lower than signal
            drift_pct = (signal_price - current_market_price) / signal_price
        else:
            return {
                "allowed": False,
                "reason": "INVALID_SIDE",
                "side": side
            }

        if drift_pct > self.max_price_drift_pct:
            return {
                "allowed": False,
                "reason": "ADVERSE_PRICE_DRIFT",
                "drift_pct": round(drift_pct, 6),
                "max_drift_pct": self.max_price_drift_pct,
                "signal_price": signal_price,
                "current_price": current_market_price
            }

        return {
            "allowed": True,
            "reason": "APPROVED",
            "drift_pct": round(drift_pct, 6),
            "signal_price": signal_price,
            "current_price": current_market_price
        }
