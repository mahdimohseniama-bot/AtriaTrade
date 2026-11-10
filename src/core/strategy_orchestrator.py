from typing import Dict, Any, List

class StrategyOrchestrator:
    def __init__(self, adapter):
        self.adapter = adapter

    def calculate_sma(self, candles: List[Dict[str, Any]], period: int = 20) -> float:
        if len(candles) < period:
            return 0.0
        closes = [c['close'] for c in candles[-period:]]
        return sum(closes) / period

    def get_signal(self, symbol: str) -> str:
        candles = self.adapter.get_candles(symbol=symbol, limit=25)
        if not candles:
            return "HOLD"
        
        current_price = candles[-1]['close']
        sma = self.calculate_sma(candles, period=20)
        
        if sma == 0:
            return "HOLD"
            
        if current_price > sma * 1.001:
            return "BUY"
        elif current_price < sma * 0.999:
            return "SELL"
        return "HOLD"
