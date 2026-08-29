"""Order Flow Imbalance & Delta Analyzer Engine for AtriaTrade.

Evaluates buying vs selling aggression, candle delta, and CVD
divergences to provide institutional order flow confirmation.
"""

from typing import Any, Dict, List


class OrderFlowImbalanceEngine:
    """Calculates order flow delta, imbalances, and detects volume divergences."""

    def __init__(self, imbalance_threshold: float = 1.5):
        """
        Initialize the OrderFlowImbalanceEngine.

        :param imbalance_threshold: Ratio threshold to flag an imbalance (e.g. 1.5 = 60/40 ratio).
        """
        self.imbalance_threshold = float(imbalance_threshold)

    def estimate_candle_delta(self, candle: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate buying and selling volume from OHLCV data using price spread & wick distribution.

        :param candle: Dict with 'open', 'high', 'low', 'close', 'volume'.
        :return: Dict containing 'buy_vol', 'sell_vol', 'delta', and 'imbalance_ratio'.
        """
        high_p = float(candle.get("high", 0.0))
        low_p = float(candle.get("low", 0.0))
        close_p = float(candle.get("close", 0.0))
        total_vol = float(candle.get("volume", 0.0))

        if total_vol <= 0.0:
            return {"buy_vol": 0.0, "sell_vol": 0.0, "delta": 0.0, "imbalance_ratio": 1.0}

        candle_range = high_p - low_p
        if candle_range <= 0.0:
            half = round(total_vol / 2.0, 4)
            return {"buy_vol": half, "sell_vol": half, "delta": 0.0, "imbalance_ratio": 1.0}

        # Estimate buy/sell bias based on close location relative to candle range
        buy_weight = (close_p - low_p) / candle_range
        buy_weight = max(0.0, min(1.0, buy_weight))
        sell_weight = 1.0 - buy_weight

        buy_vol = round(total_vol * buy_weight, 4)
        sell_vol = round(total_vol * sell_weight, 4)
        delta = round(buy_vol - sell_vol, 4)

        if sell_vol > 0:
            imbalance_ratio = round(buy_vol / sell_vol, 4)
        else:
            imbalance_ratio = 999.0

        return {
            "buy_vol": buy_vol,
            "sell_vol": sell_vol,
            "delta": delta,
            "imbalance_ratio": imbalance_ratio,
        }

    def analyze_order_flow(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a series of candles for cumulative volume delta and imbalance state.

        :param candles: List of OHLCV candle dicts in chronological order.
        :return: Analysis dictionary with CVD, current imbalance, and flags.
        """
        if not candles:
            return {
                "status": "INSUFFICIENT_DATA",
                "current_delta": 0.0,
                "cumulative_delta": 0.0,
                "imbalance_state": "NEUTRAL",
                "is_divergence": False,
            }

        cvd_series = []
        running_cvd = 0.0

        for c in candles:
            res = self.estimate_candle_delta(c)
            running_cvd += res["delta"]
            cvd_series.append(running_cvd)

        latest_candle = candles[-1]
        latest_res = self.estimate_candle_delta(latest_candle)
        latest_delta = latest_res["delta"]
        latest_ratio = latest_res["imbalance_ratio"]

        # Determine Imbalance State
        if latest_ratio >= self.imbalance_threshold:
            imbalance_state = "BUYING_IMBALANCE"
        elif latest_ratio <= (1.0 / self.imbalance_threshold):
            imbalance_state = "SELLING_IMBALANCE"
        else:
            imbalance_state = "BALANCED"

        # Check for divergence between Price and CVD across the window
        is_divergence = False
        if len(candles) >= 3:
            p_start = float(candles[0]["close"])
            p_end = float(candles[-1]["close"])
            cvd_start = cvd_series[0]
            cvd_end = cvd_series[-1]

            # Bearish Divergence: Price Made Higher High/Close, but CVD is Lower
            if p_end > p_start and cvd_end < cvd_start:
                is_divergence = True
            # Bullish Divergence: Price Made Lower Low/Close, but CVD is Higher
            elif p_end < p_start and cvd_end > cvd_start:
                is_divergence = True

        return {
            "status": "VALID",
            "current_delta": latest_delta,
            "cumulative_delta": round(running_cvd, 4),
            "imbalance_state": imbalance_state,
            "imbalance_ratio": latest_ratio,
            "is_divergence": is_divergence,
        }
