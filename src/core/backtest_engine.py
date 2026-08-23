"""
موتور بک‌تست AtriaTrade (Backtesting Engine)
==============================================
شبیه‌سازی و ارزیابی استراتژی‌ها بر روی داده‌های تاریخی کندل:
- دریافت داده‌های کندل استیک (OHLCV)
- اعمال منطق ورود و خروج معامله
- محاسبه متریک‌های استاندارد عملکرد (Win Rate، Max Drawdown، Profit Factor، Sharpe Ratio)
- بدون ریسک مالی و کاملاً آفلاین
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class BacktestTrade:
    """اطلاعات یک معامله در بک‌تست"""
    trade_id: int
    symbol: str
    side: str              # BUY يا SELL
    entry_time: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    exit_time: str = ""
    exit_price: float = 0.0
    pnl: float = 0.0
    return_pct: float = 0.0
    reason: str = ""       # TP, SL, SIGNAL, END_OF_DATA


class BacktestEngine:
    """موتور پردازش داده‌های تاریخی و اجرای استراتژی"""

    def __init__(self, initial_capital: float = 10000.0, fee_rate: float = 0.001,
                 max_risk_per_trade: float = 0.02, max_position_value: float = 5000.0):
        if initial_capital <= 0:
            raise ValueError("سرمایه اولیه باید بزرگ‌تر از صفر باشد")
        if fee_rate < 0:
            raise ValueError("کارمزد نمی‌تواند منفی باشد")
        if not 0 < max_risk_per_trade <= 0.1:
            raise ValueError("ریسک هر معامله باید بین 0 و 0.1 باشد")

        self.initial_capital = float(initial_capital)
        self.fee_rate = float(fee_rate)
        self.max_risk_per_trade = float(max_risk_per_trade)
        self.max_position_value = float(max_position_value)

        self.cash = float(initial_capital)
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[float] = [float(initial_capital)]

    def run(self, symbol: str, candles: List[Dict[str, Any]], strategy) -> Dict[str, Any]:
        """
        اجرای بک‌تست روی لیست کندل‌ها
        ساختار هر کندل باید شامل: timestamp, open, high, low, close, volume باشد.
        """
        if not candles:
            raise ValueError("لیست کندل‌ها خالی است")

        self.cash = float(self.initial_capital)
        self.trades = []
        self.equity_curve = [float(self.initial_capital)]

        current_trade: Optional[BacktestTrade] = None
        trade_counter = 1
        history_closes: List[float] = []

        for i, candle in enumerate(candles):
            timestamp = candle.get("timestamp", str(i))
            high = float(candle["high"])
            low = float(candle["low"])
            close = float(candle["close"])
            history_closes.append(close)

            # ۱. بررسی حد سود و حد ضرر پوزیشن باز با High و Low کندل جاری
            if current_trade is not None:
                closed = False
                if current_trade.side == "BUY":
                    if current_trade.stop_loss > 0 and low <= current_trade.stop_loss:
                        self._close_position(current_trade, current_trade.stop_loss, timestamp, "STOP_LOSS")
                        closed = True
                    elif current_trade.take_profit > 0 and high >= current_trade.take_profit:
                        self._close_position(current_trade, current_trade.take_profit, timestamp, "TAKE_PROFIT")
                        closed = True
                else:  # SELL
                    if current_trade.stop_loss > 0 and high >= current_trade.stop_loss:
                        self._close_position(current_trade, current_trade.stop_loss, timestamp, "STOP_LOSS")
                        closed = True
                    elif current_trade.take_profit > 0 and low <= current_trade.take_profit:
                        self._close_position(current_trade, current_trade.take_profit, timestamp, "TAKE_PROFIT")
                        closed = True

                if closed:
                    current_trade = None

            # ۲. دریافت سیگنال از استراتژی
            signal = strategy.generate_signal(history_closes)

            # ۳. پردازش خروج بر اساس سیگنال معکوس
            if current_trade is not None:
                if (current_trade.side == "BUY" and signal == "SELL") or \
                   (current_trade.side == "SELL" and signal == "BUY"):
                    self._close_position(current_trade, close, timestamp, "SIGNAL")
                    current_trade = None

            # ۴. ورود به معامله جدید در صورت نبود پوزیشن باز
            if current_trade is None and signal in ("BUY", "SELL"):
                tp, sl = 0.0, 0.0
                if hasattr(strategy, "get_tp_sl"):
                    tp, sl = strategy.get_tp_sl(signal, close)

                # محاسبه حجم ورود
                risk_amount = self.cash * self.max_risk_per_trade
                if sl > 0 and abs(close - sl) > 0:
                    quantity = risk_amount / abs(close - sl)
                else:
                    quantity = risk_amount / (close * 0.02)  # پیش‌فرض ۲ درصد فاصله

                max_qty = self.max_position_value / close
                quantity = min(quantity, max_qty, self.cash / close)
                quantity = round(quantity, 6)

                cost = quantity * close
                fee = cost * self.fee_rate
                if cost + fee <= self.cash and quantity > 0:
                    self.cash -= (cost + fee)
                    current_trade = BacktestTrade(
                        trade_id=trade_counter,
                        symbol=symbol,
                        side=signal,
                        entry_time=timestamp,
                        entry_price=close,
                        quantity=quantity,
                        stop_loss=sl,
                        take_profit=tp
                    )
                    self.trades.append(current_trade)
                    trade_counter += 1

            # ثبت ارزش دارایی
            floating_pnl = 0.0
            if current_trade is not None:
                if current_trade.side == "BUY":
                    floating_pnl = (close - current_trade.entry_price) * current_trade.quantity
                else:
                    floating_pnl = (current_trade.entry_price - close) * current_trade.quantity
            equity = self.cash + (current_trade.quantity * current_trade.entry_price if current_trade else 0.0) + floating_pnl
            self.equity_curve.append(round(equity, 2))

        # بستن پوزیشن باز باقی‌مانده در انتهای داده‌ها
        if current_trade is not None:
            last_candle = candles[-1]
            self._close_position(current_trade, float(last_candle["close"]),
                                 last_candle.get("timestamp", "END"), "END_OF_DATA")

        return self.calculate_metrics()

    def _close_position(self, trade: BacktestTrade, exit_price: float, exit_time: str, reason: str):
        """ثبت خروج و به‌روزرسانی نقدینگی با کسر کارمزد"""
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        trade.reason = reason

        gross_value = trade.quantity * exit_price
        fee = gross_value * self.fee_rate

        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity - (fee + (trade.quantity * trade.entry_price * self.fee_rate))
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity - (fee + (trade.quantity * trade.entry_price * self.fee_rate))

        trade.pnl = round(pnl, 2)
        invested = trade.quantity * trade.entry_price
        trade.return_pct = round((pnl / invested) * 100, 2) if invested > 0 else 0.0

        # بازگشت سرمایه معامله و سود/زیان خالص به صندوق نقدینگی
        self.cash = round(self.cash + invested + trade.pnl, 2)

    def calculate_metrics(self) -> Dict[str, Any]:
        """محاسبه خروجی‌های آماری عملکرد بک‌تست"""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "initial_capital": self.initial_capital,
                "final_equity": self.initial_capital,
                "total_net_pnl": 0.0,
                "total_return_pct": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0
            }

        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]

        total_net_pnl = round(sum(t.pnl for t in self.trades), 2)
        final_equity = round(self.initial_capital + total_net_pnl, 2)
        total_return_pct = round((total_net_pnl / self.initial_capital) * 100, 2)

        win_rate = round((len(wins) / total_trades) * 100, 2)

        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 0.0)

        # محاسبه Maximum Drawdown
        peak = self.equity_curve[0]
        max_dd = 0.0
        for eq in self.equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        max_drawdown_pct = round(max_dd * 100, 2)

        # محاسبه تقریب Sharpe Ratio
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1]
            if prev > 0:
                returns.append((self.equity_curve[i] - prev) / prev)

        sharpe = 0.0
        if len(returns) > 1:
            mean_r = sum(returns) / len(returns)
            variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = math.sqrt(variance)
            if std_dev > 0:
                sharpe = round((mean_r / std_dev) * math.sqrt(252), 2)  # استاندارد سالانه

        return {
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_net_pnl": total_net_pnl,
            "total_return_pct": total_return_pct,
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe
        }
