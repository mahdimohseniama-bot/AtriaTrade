from typing import Dict, Any, List, Optional


class OrderFlowAnalyzer:
    """
    تحلیل‌گر عدم تعادل جریان سفارشات (Order Flow Imbalance - OFI)
    و ساختار خرد بازار (Microstructure Analysis).
    """

    def __init__(self, depth_levels: int = 5, imbalance_threshold: float = 0.3):
        self.depth_levels = max(1, depth_levels)
        self.imbalance_threshold = float(imbalance_threshold)
        self._prev_bids: List[List[float]] = []
        self._prev_asks: List[List[float]] = []

    def calculate_static_imbalance(self, bids: List[List[float]], asks: List[List[float]]) -> float:
        """
        محاسبه عدم تعادل ایستا (Static Imbalance) در عمق مشخص:
        (Total Bid Vol - Total Ask Vol) / (Total Bid Vol + Total Ask Vol)
        محدوده خروجی بین -1.0 (فشار فروش) تا +1.0 (فشار خرید).
        """
        if not bids or not asks:
            return 0.0

        n_bids = bids[: self.depth_levels]
        n_asks = asks[: self.depth_levels]

        total_bid_vol = sum(float(b[1]) for b in n_bids if len(b) >= 2)
        total_ask_vol = sum(float(a[1]) for a in n_asks if len(a) >= 2)

        total_vol = total_bid_vol + total_ask_vol
        if total_vol <= 0:
            return 0.0

        return (total_bid_vol - total_ask_vol) / total_vol

    def calculate_delta_ofi(self, current_bids: List[List[float]], current_asks: List[List[float]]) -> float:
        """
        محاسبه تغییرات پویای جریان سفارشات بر اساس تغییرات در سطوح Best Bid و Best Ask (OFI کلاسیک).
        """
        if not current_bids or not current_asks:
            return 0.0

        if not self._prev_bids or not self._prev_asks:
            self._prev_bids = current_bids
            self._prev_asks = current_asks
            return 0.0

        prev_bid_p, prev_bid_v = float(self._prev_bids[0][0]), float(self._prev_bids[0][1])
        curr_bid_p, curr_bid_v = float(current_bids[0][0]), float(current_bids[0][0])
        # تصحیح ایندکس ولوم
        curr_bid_v = float(current_bids[0][1])

        prev_ask_p, prev_ask_v = float(self._prev_asks[0][0]), float(self._prev_asks[0][1])
        curr_ask_p, curr_ask_v = float(current_asks[0][0]), float(current_asks[0][1])

        # محاسبه دلتای سمت تقاضا (Bid Delta)
        if curr_bid_p > prev_bid_p:
            delta_bid = curr_bid_v
        elif curr_bid_p == prev_bid_p:
            delta_bid = curr_bid_v - prev_bid_v
        else:
            delta_bid = -prev_bid_v

        # محاسبه دلتای سمت عرضه (Ask Delta)
        if curr_ask_p < prev_ask_p:
            delta_ask = curr_ask_v
        elif curr_ask_p == prev_ask_p:
            delta_ask = curr_ask_v - prev_ask_v
        else:
            delta_ask = -prev_ask_v

        ofi = delta_bid - delta_ask

        # به روزرسانی حالت قبلی
        self._prev_bids = current_bids
        self._prev_asks = current_asks

        return ofi

    def analyze_market_pressure(self, bids: List[List[float]], asks: List[List[float]]) -> Dict[str, Any]:
        """
        تحلیل جامع وضعیت فشار بازار و بازگرداندن سیگنال‌های ریزساختاری.
        """
        imbalance = self.calculate_static_imbalance(bids, asks)
        delta_ofi = self.calculate_delta_ofi(bids, asks)

        if imbalance >= self.imbalance_threshold:
            sentiment = "BULLISH_PRESSURE"
        elif imbalance <= -self.imbalance_threshold:
            sentiment = "BEARISH_PRESSURE"
        else:
            sentiment = "NEUTRAL"

        return {
            "imbalance_ratio": round(imbalance, 4),
            "delta_ofi": round(delta_ofi, 4),
            "sentiment": sentiment,
            "is_valid": len(bids) > 0 and len(asks) > 0,
        }
