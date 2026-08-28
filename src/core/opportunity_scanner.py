"""Multi-Exchange Opportunity & Arbitrage Scanner (Paper Mode)."""

from typing import Dict, Any, List, Optional


class OpportunityScanner:
    """Scans and detects price discrepancies and arbitrage spreads across exchanges."""

    def __init__(self, min_spread_pct: float = 0.5):
        """
        Initialize scanner.
        :param min_spread_pct: Minimum net profit percentage after estimated fees to trigger signal.
        """
        self.min_spread_pct = float(min_spread_pct)

    def scan_pair_spread(
        self,
        symbol: str,
        prices: Dict[str, float],
        fee_pct: float = 0.2
    ) -> Optional[Dict[str, Any]]:
        """
        Scan a single pair across given exchange prices.
        :param symbol: Trading pair symbol (e.g. 'BTC/USDT' or 'BTC/TM')
        :param prices: Dict mapping exchange_name -> current_price
        :param fee_pct: Estimated one-way fee percentage per exchange
        :return: Opportunity dict if spread > min_spread_pct, else None
        """
        if len(prices) < 2:
            return None

        # Filter positive prices
        valid_prices = {k: v for k, v in prices.items() if v > 0}
        if len(valid_prices) < 2:
            return None

        lowest_ex = min(valid_prices, key=valid_prices.get)
        highest_ex = max(valid_prices, key=valid_prices.get)

        buy_price = valid_prices[lowest_ex]
        sell_price = valid_prices[highest_ex]

        if buy_price <= 0:
            return None

        gross_spread_pct = ((sell_price - buy_price) / buy_price) * 100.0
        # Net spread deducting round-trip fees (buy fee + sell fee)
        net_spread_pct = gross_spread_pct - (2 * fee_pct)

        if net_spread_pct >= self.min_spread_pct:
            return {
                "symbol": symbol,
                "buy_exchange": lowest_ex,
                "buy_price": buy_price,
                "sell_exchange": highest_ex,
                "sell_price": sell_price,
                "gross_spread_pct": round(gross_spread_pct, 3),
                "net_spread_pct": round(net_spread_pct, 3),
                "action": "ARBITRAGE_OPPORTUNITY"
            }

        return None
