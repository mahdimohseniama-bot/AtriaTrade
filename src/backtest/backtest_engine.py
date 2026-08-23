"""
Backtest Engine for AtriaTrade
Runs historical simulations using strategies and paper trading logic.
"""

from typing import List, Dict, Any

class BacktestEngine:
    def __init__(self, strategy, trading_engine):
        self.strategy = strategy
        self.trading_engine = trading_engine
        self.results = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "net_profit": 0.0,
            "closed_trades": [],
        }

    def run(self, historical_data: List[Dict[str, Any]], symbol: str = "BTCUSDT"):
        """
        Run backtest on historical candle data.
        historical_data must be a list of OHLCV dictionaries.
        """
        if not historical_data or len(historical_data) < 5:
            raise ValueError("Not enough historical data for backtest")

        for i in range(5, len(historical_data)):
            window = historical_data[:i+1]
            signal = self.strategy.generate_signal(window)

            current_price = float(window[-1]["close"])

            if signal == "BUY":
                result = self.trading_engine.buy(symbol=symbol, price=current_price)
                if result:
                    self.results["total_trades"] += 1

            elif signal == "SELL":
                result = self.trading_engine.sell(symbol=symbol, price=current_price)
                if result:
                    self.results["total_trades"] += 1

        closed_trades = self.trading_engine.get_closed_trades()
        self.results["closed_trades"] = closed_trades

        wins = 0
        losses = 0
        net_profit = 0.0

        for trade in closed_trades:
            pnl = trade.get("pnl", 0.0)
            net_profit += pnl
            if pnl >= 0:
                wins += 1
            else:
                losses += 1

        self.results["wins"] = wins
        self.results["losses"] = losses
        self.results["net_profit"] = net_profit

        return self.results

    def get_summary(self):
        total_closed = len(self.results["closed_trades"])
        win_rate = (self.results["wins"] / total_closed * 100) if total_closed > 0 else 0.0

        return {
            "total_trades": self.results["total_trades"],
            "closed_trades": total_closed,
            "wins": self.results["wins"],
            "losses": self.results["losses"],
            "win_rate_percent": round(win_rate, 2),
            "net_profit": round(self.results["net_profit"], 2),
        }
