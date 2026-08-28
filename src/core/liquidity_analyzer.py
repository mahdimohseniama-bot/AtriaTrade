from typing import List, Tuple, Dict, Any, Optional


class OrderbookDepthAnalyzer:
    """
    Analyzes orderbook depth, order flow imbalance, and liquidity walls.
    """
    def __init__(self, depth_limit: int = 20):
        self.depth_limit = depth_limit

    def calculate_imbalance(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]]
    ) -> float:
        """
        Calculates orderbook volume imbalance.
        Formula: (Total Bid Volume - Total Ask Volume) / (Total Bid Volume + Total Ask Volume)
        Returns a value between -1.0 (heavy sell pressure) and +1.0 (heavy buy pressure).
        """
        top_bids = bids[:self.depth_limit]
        top_asks = asks[:self.depth_limit]

        bid_vol = sum(volume for _, volume in top_bids)
        ask_vol = sum(volume for _, volume in top_asks)
        total_vol = bid_vol + ask_vol

        if total_vol == 0:
            return 0.0

        return (bid_vol - ask_vol) / total_vol

    def calculate_effective_vwap(
        self,
        orders: List[Tuple[float, float]],
        target_qty: float
    ) -> Optional[float]:
        """
        Calculates VWAP for consuming target_qty from the book (bids for sell, asks for buy).
        """
        if target_qty <= 0:
            return None

        remaining_qty = target_qty
        total_cost = 0.0

        for price, volume in orders:
            fill_qty = min(remaining_qty, volume)
            total_cost += fill_qty * price
            remaining_qty -= fill_qty

            if remaining_qty <= 1e-9:
                break

        if remaining_qty > 1e-9:
            # Not enough liquidity in the provided depth
            return None

        return total_cost / target_qty

    def detect_liquidity_walls(
        self,
        orders: List[Tuple[float, float]],
        threshold_multiplier: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Finds price levels where order size is significantly higher than the average.
        """
        if not orders:
            return []

        volumes = [vol for _, vol in orders]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0.0

        walls = []
        for price, vol in orders:
            if avg_volume > 0 and vol >= (avg_volume * threshold_multiplier):
                walls.append({
                    "price": price,
                    "volume": vol,
                    "multiple_of_avg": round(vol / avg_volume, 2)
                })

        return walls

    def estimate_market_impact_slippage(
        self,
        asks: List[Tuple[float, float]],
        order_qty: float,
        best_ask: float
    ) -> float:
        """
        Estimates percentage slippage for a market BUY order.
        """
        vwap = self.calculate_effective_vwap(asks, order_qty)
        if vwap is None or best_ask <= 0:
            return 0.0

        slippage_pct = ((vwap - best_ask) / best_ask) * 100.0
        return max(0.0, slippage_pct)
