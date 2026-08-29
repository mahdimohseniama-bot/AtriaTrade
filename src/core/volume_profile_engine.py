"""Adaptive Volume Profile & Point of Control (POC) Analyzer for AtriaTrade.

Computes Volume Profile, Point of Control (POC), Value Area High (VAH),
and Value Area Low (VAL) for dynamic institutional price-level tracking.
"""

from typing import Any, Dict, List, Optional
import math


class VolumeProfileEngine:
    """Calculates Point of Control (POC) and Value Area bounds (VAH, VAL)."""

    def __init__(self, num_bins: int = 20, value_area_pct: float = 0.70):
        """
        Initialize the VolumeProfileEngine.

        :param num_bins: Number of price bins for the profile distribution.
        :param value_area_pct: Percentage of volume defining the Value Area (default 70%).
        """
        self.num_bins = max(5, int(num_bins))
        self.value_area_pct = float(value_area_pct)

    def calculate_profile(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Volume Profile, POC, VAH, and VAL from given candle history.

        :param candles: List of OHLCV candle dicts.
        :return: Dict containing poc_price, vah_price, val_price, and profile stats.
        """
        if not candles or len(candles) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "poc_price": 0.0,
                "vah_price": 0.0,
                "val_price": 0.0,
                "total_volume": 0.0,
                "current_price_location": "UNKNOWN",
            }

        highs = [float(c.get("high", 0.0)) for c in candles]
        lows = [float(c.get("low", 0.0)) for c in candles]
        overall_high = max(highs)
        overall_low = min(lows)
        price_span = overall_high - overall_low

        if price_span <= 0.0:
            last_price = float(candles[-1].get("close", 0.0))
            total_vol = sum(float(c.get("volume", 0.0)) for c in candles)
            return {
                "status": "FLAT_MARKET",
                "poc_price": last_price,
                "vah_price": last_price,
                "val_price": last_price,
                "total_volume": total_vol,
                "current_price_location": "AT_POC",
            }

        bin_size = price_span / self.num_bins
        # Bins store volume distributed across price levels
        bins = [0.0] * self.num_bins

        for c in candles:
            vol = float(c.get("volume", 0.0))
            if vol <= 0:
                continue
            c_high = float(c.get("high", 0.0))
            c_low = float(c.get("low", 0.0))
            c_span = c_high - c_low

            if c_span <= 0.0:
                # Distribute to single bin containing the price
                idx = int((c_high - overall_low) / bin_size)
                idx = min(self.num_bins - 1, max(0, idx))
                bins[idx] += vol
            else:
                # Distribute volume evenly across the bins overlapped by the candle
                start_idx = int((c_low - overall_low) / bin_size)
                end_idx = int((c_high - overall_low) / bin_size)
                start_idx = min(self.num_bins - 1, max(0, start_idx))
                end_idx = min(self.num_bins - 1, max(0, end_idx))
                overlap_count = max(1, (end_idx - start_idx + 1))
                vol_slice = vol / overlap_count

                for i in range(start_idx, end_idx + 1):
                    bins[i] += vol_slice

        total_volume = sum(bins)
        if total_volume <= 0.0:
            last_price = float(candles[-1].get("close", 0.0))
            return {
                "status": "ZERO_VOLUME",
                "poc_price": last_price,
                "vah_price": last_price,
                "val_price": last_price,
                "total_volume": 0.0,
                "current_price_location": "UNKNOWN",
            }

        # Determine POC (Bin with max volume)
        poc_idx = bins.index(max(bins))
        poc_price = round(overall_low + (poc_idx + 0.5) * bin_size, 4)

        # Determine Value Area (70% total volume radiating from POC)
        target_va_vol = total_volume * self.value_area_pct
        accumulated_vol = bins[poc_idx]
        va_low_idx = poc_idx
        va_high_idx = poc_idx

        while accumulated_vol < target_va_vol and (va_low_idx > 0 or va_high_idx < self.num_bins - 1):
            next_above = bins[va_high_idx + 1] if va_high_idx < self.num_bins - 1 else -1.0
            next_below = bins[va_low_idx - 1] if va_low_idx > 0 else -1.0

            if next_above >= next_below and next_above >= 0:
                va_high_idx += 1
                accumulated_vol += next_above
            elif next_below > next_above and next_below >= 0:
                va_low_idx -= 1
                accumulated_vol += next_below
            else:
                break

        val_price = round(overall_low + va_low_idx * bin_size, 4)
        vah_price = round(overall_low + (va_high_idx + 1) * bin_size, 4)

        current_close = float(candles[-1].get("close", 0.0))
        if current_close > vah_price:
            loc = "ABOVE_VALUE_AREA"
        elif current_close < val_price:
            loc = "BELOW_VALUE_AREA"
        else:
            loc = "INSIDE_VALUE_AREA"

        return {
            "status": "VALID",
            "poc_price": poc_price,
            "vah_price": vah_price,
            "val_price": val_price,
            "total_volume": round(total_volume, 4),
            "current_price_location": loc,
        }
