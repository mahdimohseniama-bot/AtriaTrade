"""
Multi-Timeframe Fractal Breaker Block Engine (Capability 92)
Identifies failed order blocks transformed into institutional breaker blocks (support-to-resistance / resistance-to-support flip zones)
following liquidity sweeps.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class BreakerBlock:
    breaker_id: str
    symbol: str
    timeframe: str
    breaker_type: str  # BULLISH_BREAKER or BEARISH_BREAKER
    top_price: float
    bottom_price: float
    sweep_high_or_low: float
    is_mitigated: bool = False
    mitigation_count: int = 0
    status: str = "ACTIVE"  # ACTIVE, MITIGATED, INVALIDATED

class BreakerBlockEngine:
    def __init__(self, max_mitigations: int = 2):
        """
        :param max_mitigations: Maximum number of retests before breaker block is considered exhausted/mitigated.
        """
        self.max_mitigations = max_mitigations
        self.breakers: List[BreakerBlock] = []

    def identify_bullish_breaker(
        self,
        symbol: str,
        timeframe: str,
        failed_ob_high: float,
        failed_ob_low: float,
        liquidity_sweep_low: float,
        breakout_price: float
    ) -> Optional[BreakerBlock]:
        """
        Bullish Breaker:
        Price sweeps previous low (Stop hunt), then strongly breaks above the previous down-candle (failed Bearish OB).
        Now this failed OB zone becomes strong Bullish Support on retest.
        """
        if failed_ob_high <= failed_ob_low or liquidity_sweep_low >= failed_ob_low:
            return None

        # Confirmed only if price broke strongly above the failed OB high
        if breakout_price <= failed_ob_high:
            return None

        breaker_id = f"BRK_BULL_{symbol}_{timeframe}_{len(self.breakers) + 1}"
        breaker = BreakerBlock(
            breaker_id=breaker_id,
            symbol=symbol,
            timeframe=timeframe,
            breaker_type="BULLISH_BREAKER",
            top_price=round(failed_ob_high, 4),
            bottom_price=round(failed_ob_low, 4),
            sweep_high_or_low=round(liquidity_sweep_low, 4),
            is_mitigated=False,
            mitigation_count=0,
            status="ACTIVE"
        )
        self.breakers.append(breaker)
        return breaker

    def identify_bearish_breaker(
        self,
        symbol: str,
        timeframe: str,
        failed_ob_high: float,
        failed_ob_low: float,
        liquidity_sweep_high: float,
        breakout_price: float
    ) -> Optional[BreakerBlock]:
        """
        Bearish Breaker:
        Price sweeps previous high (Stop hunt), then strongly breaks below the previous up-candle (failed Bullish OB).
        Now this failed OB zone becomes strong Bearish Resistance on retest.
        """
        if failed_ob_high <= failed_ob_low or liquidity_sweep_high <= failed_ob_high:
            return None

        # Confirmed only if price broke strongly below the failed OB low
        if breakout_price >= failed_ob_low:
            return None

        breaker_id = f"BRK_BEAR_{symbol}_{timeframe}_{len(self.breakers) + 1}"
        breaker = BreakerBlock(
            breaker_id=breaker_id,
            symbol=symbol,
            timeframe=timeframe,
            breaker_type="BEARISH_BREAKER",
            top_price=round(failed_ob_high, 4),
            bottom_price=round(failed_ob_low, 4),
            sweep_high_or_low=round(liquidity_sweep_high, 4),
            is_mitigated=False,
            mitigation_count=0,
            status="ACTIVE"
        )
        self.breakers.append(breaker)
        return breaker

    def evaluate_retest(self, breaker: BreakerBlock, test_price: float) -> BreakerBlock:
        """
        Checks if current price is testing/mitigating or invalidating the breaker block.
        """
        if breaker.status != "ACTIVE":
            return breaker

        if breaker.breaker_type == "BULLISH_BREAKER":
            # Invalidated if price breaks cleanly below bottom of bullish breaker
            if test_price < breaker.bottom_price:
                breaker.status = "INVALIDATED"
            # Retest / Mitigation zone
            elif breaker.bottom_price <= test_price <= breaker.top_price:
                breaker.mitigation_count += 1
                if breaker.mitigation_count >= self.max_mitigations:
                    breaker.is_mitigated = True
                    breaker.status = "MITIGATED"
        else:  # BEARISH_BREAKER
            # Invalidated if price breaks cleanly above top of bearish breaker
            if test_price > breaker.top_price:
                breaker.status = "INVALIDATED"
            # Retest / Mitigation zone
            elif breaker.bottom_price <= test_price <= breaker.top_price:
                breaker.mitigation_count += 1
                if breaker.mitigation_count >= self.max_mitigations:
                    breaker.is_mitigated = True
                    breaker.status = "MITIGATED"

        return breaker

    def get_active_breakers(self, symbol: str, timeframe: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns active actionable breaker blocks.
        """
        results = []
        for b in self.breakers:
            if b.symbol == symbol and b.status == "ACTIVE":
                if timeframe is None or b.timeframe == timeframe:
                    results.append({
                        "breaker_id": b.breaker_id,
                        "timeframe": b.timeframe,
                        "type": b.breaker_type,
                        "zone_top": b.top_price,
                        "zone_bottom": b.bottom_price,
                        "mitigations": b.mitigation_count
                    })
        return results
