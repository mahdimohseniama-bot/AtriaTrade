import logging
from typing import Dict, Any, List, Optional
from src.core.fvg_detector import FVGDetector, Candle
from src.core.ote_engine import OTEEngine, TradeDirection
from src.core.risk_manager import RiskManager, RiskConfig

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fvg_detector = FVGDetector(min_gap_percent=0.1)
        self.ote_engine = OTEEngine(sweet_spot=0.705)
        self.risk_manager = RiskManager(config=RiskConfig(total_capital=self.config.get("initial_balance", 1000.0)))
        logger.info("TradingEngine initialized (Lightweight Native SMC + Risk).")

    def analyze_market_data(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحلیل سبک SMC بدون نیاز به دیتای حجیم یا پانداس"""
        if not candles or len(candles) < 3:
            return {"action": "HOLD", "reason": "Insufficient candle data"}

        candle_objs = [
            Candle(
                open=c['open'],
                high=c['high'],
                low=c['low'],
                close=c['close'],
                timestamp=c.get('timestamp', 0)
            ) for c in candles
        ]

        # 1. تشخیص FVG
        fvgs = self.fvg_detector.detect_fvgs(candle_objs)

        # 2. محاسبه OTE
        high = max(c.high for c in candle_objs)
        low = min(c.low for c in candle_objs)
        current_price = candle_objs[-1].close

        ote_profile = self.ote_engine.calculate_ote(
            swing_low=low,
            swing_high=high,
            direction=TradeDirection.BULLISH
        )

        in_ote = self.ote_engine.is_in_ote_zone(current_price, ote_profile)

        action = "HOLD"
        reason = "Scanning for SMC confluence"

        bullish_fvgs = [f for f in fvgs if f.fvg_type.value == "bullish"]

        if bullish_fvgs and in_ote:
            action = "BUY"
            reason = "Confluence: Bullish FVG in OTE sweet zone"
        elif not in_ote:
            reason = "Price out of OTE premium/discount range"

        # 3. مدیریت ریسک و محاسبه حجم مجاز ورود
        stop_loss = current_price * 0.985
        take_profit = current_price * 1.03

        size_result = self.risk_manager.calculate_position_size(
            entry_price=current_price,
            stop_loss=stop_loss,
            capital=self.config.get("initial_balance", 1000.0),
            side="BUY"
        )
        pos_size = size_result.get("units", 0) if isinstance(size_result, dict) else size_result

        return {
            "action": action,
            "reason": reason,
            "symbol": self.config.get("symbol", "USDT-IRT"),
            "current_price": current_price,
            "suggested_position_size": pos_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "active_fvgs_count": len(fvgs)
        }
