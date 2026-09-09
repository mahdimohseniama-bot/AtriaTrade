import time
from typing import List, Dict, Any, Optional
from src.core.fvg_detector import FVGDetector, Candle, FVGType
from src.core.smc_structure_engine import SMCStructureEngine, OrderBlockType
from src.core.smc_composite_engine import SMCCompositeEngine, SMCCompositeSignal
from src.core.dynamic_leverage_engine import DynamicLeverageEngine
from src.core.capital_manager import CapitalManager

class LiveTradingPipeline:
    def __init__(self, capital_manager: CapitalManager, min_score: float = 60.0):
        self.capital_mgr = capital_manager
        self.fvg_detector = FVGDetector(min_gap_percent=0.05)
        self.smc_engine = SMCStructureEngine(swing_lookback=3)
        self.composite_engine = SMCCompositeEngine(min_confidence_score=min_score)
        self.leverage_engine = DynamicLeverageEngine(max_risk_per_trade_pct=0.02, max_leverage=10.0)

    def analyze_and_execute(self, symbol: str, raw_candles: List[Dict[str, float]]) -> Optional[Dict[str, Any]]:
        """
        دریافت کندل‌های زنده، تحلیل پیشرفته SMC و صدور اردر با حجم و لوریج بهینه
        """
        if len(raw_candles) < 5:
            return {"status": "INSUFFICIENT_DATA", "symbol": symbol}

        candles = [
            Candle(
                open=c['open'],
                high=c['high'],
                low=c['low'],
                close=c['close'],
                timestamp=int(c.get('timestamp', time.time()))
            ) for c in raw_candles
        ]

        current_candle = candles[-1]
        current_price = current_candle.close

        # ۱. تحلیل ساختار سویینگ‌ها برای تعیین محدوده Range High و Low
        highs, lows = self.smc_engine.find_swing_highs_lows(candles)
        recent_highs = [p for _, p in highs] if highs else [max(c.high for c in candles)]
        recent_lows = [p for _, p in lows] if lows else [min(c.low for c in candles)]
        
        range_high = max(recent_highs)
        range_low = min(recent_lows)
        
        if range_high <= range_low:
            range_high = current_price * 1.02
            range_low = current_price * 0.98

        # ۲. تشخیص اوردر بلاک‌ها (Order Blocks)
        obs = self.smc_engine.detect_order_blocks(candles)
        ob_detected = False
        ob_direction = None
        if obs:
            last_ob = obs[-1]
            ob_detected = True
            ob_direction = "BUY" if last_ob.ob_type == OrderBlockType.BULLISH else "SELL"

        # ۳. تشخیص FVG (Fair Value Gaps)
        fvgs = self.fvg_detector.detect_fvgs(candles)
        fvg_detected = False
        fvg_direction = None
        if fvgs:
            unmitigated = [f for f in fvgs if not f.is_mitigated]
            if unmitigated:
                last_fvg = unmitigated[-1]
                fvg_detected = True
                fvg_direction = "BUY" if last_fvg.gap_type == FVGType.BULLISH else "SELL"

        # ۴. صدور سیگنال مرکب توسط موتور اصلی SMC
        signal: SMCCompositeSignal = self.composite_engine.generate_signal(
            symbol=symbol,
            current_price=current_price,
            range_high=range_high,
            range_low=range_low,
            fvg_detected=fvg_detected,
            fvg_direction=fvg_direction,
            ob_detected=ob_detected,
            ob_direction=ob_direction,
            ote_aligned=True,
            liquidity_swept=True
        )

        if signal.direction == "NEUTRAL" or signal.confidence in ["REJECTED", "LOW"]:
            return {
                "status": "NO_TRADE",
                "symbol": symbol,
                "reason": signal.rejection_reason or f"Low confidence ({signal.score} pts)"
            }

        # ۵. مدیریت سرمایه و لوریج داینامیک
        equity = self.capital_mgr.get_working_capital()
        allocated_margin = self.capital_mgr.allocate_trade_capital()

        sizing = self.leverage_engine.calculate_sizing(
            account_equity=equity,
            entry_price=signal.entry_price,
            stop_loss_price=signal.stop_loss,
            allocated_margin=allocated_margin
        )

        return {
            "status": "ORDER_GENERATED",
            "symbol": symbol,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "score": signal.score,
            "confluences": signal.confluences,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "sizing": sizing
        }
