"""
موتور معاملات آزمایشی AtriaTrade (Paper Trading Engine)
=======================================================
شبیه‌سازی کامل معاملات بدون پول واقعی:
- دریافت قیمت نمادها
- تولید سیگنال خرید/فروش (میانگین متحرک ساده یا استراتژی خارجی)
- باز کردن معامله با محاسبه حجم از روی ریسک
- اعمال خودکار Take Profit و Stop Loss
- ثبت و ذخیره نتیجه معاملات در فایل JSON

فقط برای Paper Trading / Testnet استفاده شود.
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime

# مسیر پوشه داده پروژه: ~/AtriaTrade/data
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")


@dataclass
class Trade:
    """اطلاعات یک معامله"""

    trade_id: str
    symbol: str
    side: str                 # BUY يا SELL
    entry_price: float        # قيمت ورود
    quantity: float           # حجم
    stop_loss: float          # حد ضرر
    take_profit: float        # حد سود
    opened_at: str            # زمان باز شدن
    status: str = "OPEN"      # OPEN يا CLOSED
    exit_price: float = 0.0   # قيمت خروج
    pnl: float = 0.0          # سود/زيان نهايي
    reason: str = ""          # دليل بسته شدن
    closed_at: str = ""       # زمان بسته شدن


class PaperTradingEngine:
    """موتور شبيه‌سازي معاملات"""

    def __init__(self, initial_capital=10000.0, max_position_value=5000.0,
                 risk_per_trade=0.02, data_dir=None):
        if initial_capital <= 0:
            raise ValueError("سرمایه اولیه باید بزرگ‌تر از صفر باشد")
        if max_position_value <= 0:
            raise ValueError("سقف ارزش پوزیشن باید بزرگ‌تر از صفر باشد")
        if not 0 < risk_per_trade <= 0.1:
            raise ValueError("نرخ ریسک باید بین 0 و 0.1 باشد")

        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.max_position_value = float(max_position_value)
        self.risk_per_trade = float(risk_per_trade)
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.trades = []
        self.prices = {}
        self.price_history = {}
        self.strategy = None

    # ---------- مدیریت قیمت ----------

    def update_price(self, symbol, price):
        """به‌روزرسانی قیمت نماد و بررسی خودکار حد سود/ضرر"""
        if price <= 0:
            raise ValueError("قیمت باید بزرگ‌تر از صفر باشد")
        self.prices[symbol] = float(price)
        self.price_history.setdefault(symbol, []).append(float(price))
        return self._check_tp_sl()

    # ---------- سیگنال ----------

    def set_strategy(self, strategy):
        """اتصال استراتژی خارجی (باید متد generate_signal(prices) داشته باشد)"""
        self.strategy = strategy

    def generate_signal(self, symbol):
        """سیگنال معاملاتی: BUY، SELL یا HOLD"""
        if self.strategy is not None:
            signal = self.strategy.generate_signal(self.price_history.get(symbol, []))
            return signal if signal in ("BUY", "SELL", "HOLD") else "HOLD"
        return self._default_signal(symbol)

    def _default_signal(self, symbol):
        """سیگنال پیش‌فرض با مقایسه میانگین متحرک ۵ و ۲۰"""
        prices = self.price_history.get(symbol, [])
        if len(prices) < 20:
            return "HOLD"
        short_sma = sum(prices[-5:]) / 5
        long_sma = sum(prices[-20:]) / 20
        if short_sma > long_sma:
            return "BUY"
        if short_sma < long_sma:
            return "SELL"
        return "HOLD"

    # ---------- باز کردن معامله ----------

    def open_trade(self, symbol, side="BUY", price=None, stop_loss=None,
                   take_profit=None, quantity=None):
        """باز کردن یک معامله شبیه‌سازی‌شده با کنترل ریسک"""
        if side not in ("BUY", "SELL"):
            raise ValueError("سمت معامله باید BUY یا SELL باشد")

        if price is None:
            price = self.prices.get(symbol)
            if price is None:
                raise ValueError(f"قیمتی برای {symbol} ثبت نشده است")

        if any(t.symbol == symbol and t.status == "OPEN" for t in self.trades):
            raise ValueError(f"هم‌اکنون یک پوزیشن باز برای {symbol} وجود دارد")

        entry = float(price)

        # اعتبارسنجی حد ضرر و حد سود
        if side == "BUY":
            if stop_loss is not None and stop_loss >= entry:
                raise ValueError("حد ضرر خرید باید پایین‌تر از قیمت ورود باشد")
            if take_profit is not None and take_profit <= entry:
                raise ValueError("حد سود خرید باید بالاتر از قیمت ورود باشد")
        else:
            if stop_loss is not None and stop_loss <= entry:
                raise ValueError("حد ضرر فروش باید بالاتر از قیمت ورود باشد")
            if take_profit is not None and take_profit >= entry:
                raise ValueError("حد سود فروش باید پایین‌تر از قیمت ورود باشد")

        # محاسبه حجم از روی ریسک
        if quantity is None:
            if stop_loss is None:
                raise ValueError("برای محاسبه حجم، حد ضرر (stop_loss) لازم است")
            risk_amount = self.cash * self.risk_per_trade
            sl_distance = abs(entry - float(stop_loss))
            if sl_distance == 0:
                raise ValueError("فاصله حد ضرر نمی‌تواند صفر باشد")
            quantity = risk_amount / sl_distance
            max_qty = self.max_position_value / entry
            quantity = min(quantity, max_qty)
        else:
            quantity = float(quantity)
            value = quantity * entry
            if value > self.max_position_value:
                raise ValueError(
                    f"ارزش پوزیشن {value:.2f} از سقف {self.max_position_value:.2f} بیشتر است"
                )

        quantity = round(quantity, 6)
        value = round(quantity * entry, 2)

        if value > self.cash:
            raise ValueError(f"نقدینگی کافی نیست: نیاز {value:.2f}، موجودی {self.cash:.2f}")

        trade = Trade(
            trade_id=f"{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            symbol=symbol,
            side=side,
            entry_price=entry,
            quantity=quantity,
            stop_loss=float(stop_loss) if stop_loss is not None else 0.0,
            take_profit=float(take_profit) if take_profit is not None else 0.0,
            opened_at=datetime.now().isoformat(),
        )
        self.trades.append(trade)
        self.cash = round(self.cash - value, 2)
        return trade

    # ---------- بستن معامله ----------

    def close_trade(self, trade_id, price=None, reason="MANUAL"):
        """بستن یک معامله باز و محاسبه سود/زیان"""
        trade = None
        for t in self.trades:
            if t.trade_id == trade_id and t.status == "OPEN":
                trade = t
                break
        if trade is None:
            raise ValueError("معامله باز با این شناسه پیدا نشد")

        exit_price = float(price) if price is not None else self.prices.get(trade.symbol)
        if exit_price is None:
            raise ValueError("قیمت خروج موجود نیست")

        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity

        trade.exit_price = exit_price
        trade.pnl = round(pnl, 2)
        trade.reason = reason
        trade.status = "CLOSED"
        trade.closed_at = datetime.now().isoformat()

        # برگرداندن وجه بلوک‌شده + سود/زیان
        self.cash = round(self.cash + trade.entry_price * trade.quantity + trade.pnl, 2)
        return trade

    def _check_tp_sl(self):
        """بررسی خودکار حد سود و حد ضرر روی همه پوزیشن‌های باز"""
        events = []
        for trade in list(self.trades):
            if trade.status != "OPEN":
                continue
            price = self.prices.get(trade.symbol)
            if price is None:
                continue
            if trade.side == "BUY":
                if trade.take_profit and price >= trade.take_profit:
                    events.append(self.close_trade(trade.trade_id, price, "TAKE_PROFIT"))
                elif trade.stop_loss and price <= trade.stop_loss:
                    events.append(self.close_trade(trade.trade_id, price, "STOP_LOSS"))
            else:
                if trade.take_profit and price <= trade.take_profit:
                    events.append(self.close_trade(trade.trade_id, price, "TAKE_PROFIT"))
                elif trade.stop_loss and price >= trade.stop_loss:
                    events.append(self.close_trade(trade.trade_id, price, "STOP_LOSS"))
        return events

    # ---------- گزارش‌گیری ----------

    def get_open_trades(self):
        return [t for t in self.trades if t.status == "OPEN"]

    def get_closed_trades(self):
        return [t for t in self.trades if t.status != "OPEN"]

    def get_trade_history(self):
        return list(self.trades)

    def get_equity(self):
        """سرمایه کل = نقدینگی + سود/زیان شناور پوزیشن‌های باز"""
        equity = self.cash
        for trade in self.get_open_trades():
            price = self.prices.get(trade.symbol, trade.entry_price)
            if trade.side == "BUY":
                equity += (price - trade.entry_price) * trade.quantity
            else:
                equity += (trade.entry_price - price) * trade.quantity
        return round(equity, 2)

    def get_total_pnl(self):
        """سود/زیان تحقق‌یافته کل"""
        return round(sum(t.pnl for t in self.get_closed_trades()), 2)

    def get_status(self):
        """گزارش خلاصه وضعیت موتور"""
        closed = self.get_closed_trades()
        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "equity": self.get_equity(),
            "total_pnl": self.get_total_pnl(),
            "open_trades": len(self.get_open_trades()),
            "closed_trades": len(closed),
            "wins": sum(1 for t in closed if t.pnl > 0),
            "losses": sum(1 for t in closed if t.pnl < 0),
        }

    # ---------- ذخیره و بازیابی ----------

    def save_state(self, path=None):
        """ذخیره وضعیت کامل موتور در فایل JSON"""
        path = path or os.path.join(self.data_dir, "trading_state.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "max_position_value": self.max_position_value,
            "risk_per_trade": self.risk_per_trade,
            "trades": [asdict(t) for t in self.trades],
            "prices": self.prices,
            "price_history": self.price_history,
            "saved_at": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return path

    def load_state(self, path=None):
        """بازیابی وضعیت موتور از فایل JSON"""
        path = path or os.path.join(self.data_dir, "trading_state.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"فایل وضعیت پیدا نشد: {path}")
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.initial_capital = state["initial_capital"]
        self.cash = state["cash"]
        self.max_position_value = state["max_position_value"]
        self.risk_per_trade = state["risk_per_trade"]
        self.trades = [Trade(**t) for t in state["trades"]]
        self.prices = state.get("prices", {})
        self.price_history = state.get("price_history", {})
        return self
