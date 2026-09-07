# -*- coding: utf-8 -*-
"""AutoPilot v2.1 — مغز مستقل AtriaTrade (فقط Paper).
- فید: زنجیرهی خودکار (wallex → nobitex → binance → fake)
- ملاک خرید: روند صعودی تأییدشده
- ملاک فروش: شکست روند OR استاپلاس OR تیکپروفیت (بر اساس entry)
- همهچیز داخل atria_state.json ذخیره میشه.
 هیچ سفارش واقعی ثبت نمیشه.
"""
import json
import logging
import threading
import time
from pathlib import Path

from src.core.live_price import LiveFeed

log = logging.getLogger("atria.autopilot")
log.setLevel(logging.INFO)
TRADES_FILE = Path("atria_state.json")


class AutoPilot:
    def __init__(self, symbol="BTC/USDT", initial_balance=1000.0,
                 source="auto", fast=2, slow=20, risk_pct=0.6,
                 cooldown=5.0, fee_pct=0.1, spread_guard=0.35,
                 stop_loss=2.0, take_profit=1.5, tick_interval=1.0:
        self.symbol = symbol
        self.initial = float(initial_balance)
        self.balance = float(initial_balance)
        self.coin = 0.0
        self.entry = 0.0
        self.prices = []
        self.trades = []
        self.wins = 0
        self.losses = 0
        self.fast_window = fast
        self.slow_window = slow
        self.risk = float(risk_pct)
        self.cooldown_sec = float(cooldown)
        self.fee = float(fee_pct) / 100.0
        self.spread_guard = float(spread_guard)
        self.stop_loss = float(stop_loss)       # درصد ضرر مجاز قبل از قطع
        self.take_profit = float(take_profit)     # درصد سود هدف
        self.tick_interval = float(tick_interval)
        self._last_buy_ts = 0.0
        self._last_price =  ​0.0
        self._last_src = source
        self.running = False
        self.thread = None
        self.feed = LiveFeed(source=source, symbol=symbol)

    # ================= میانگینها =================
    def ema(self, period):
        if not self.prices:
            return 0.0
        arr = self.prices[-period:]
        k = 2.0 / (period + 1.0)
        e = arr[0]
        for x in arr[1:]:
            e = (x - e) * k + e
        return e

    def sma(self, period):
        if not self.prices:
            return  ​0.0
        arr = self.prices[-period:]
        return sum(arr) / len(arr)

    # ================= موتور تصمیم =================
    def _decide(self, bid, ask):
        if len(self.prices) < self.slow_window + 2:
            return "HOLD", "warmup"

        mid = (bid + ask) / 2.0
        if mid <= 0:
            return "HOLD", "bad_price"

        spread_pct = (ask - bid) / mid * 100.0
        if spread_pct > self.spread_guard:
            return "HOLD", "wide_spread"

        price = self.prices[-1]
        fast_ema = self.ema(self.fast_window)
        slow_sma = self.sma(self.slow_window)

        # ---- پوزیشن باز: اول استاپلاس و تیکپروفیت چک بشه ----
        if self.coin > 0.0:
            pct = (bid - self.entry) / self.entry * 100.0
            if pct <= -self.stop_loss:
                return "SELL", "stop_loss"
            if pct >= self.take_profit:
                return "SELL", "take_profit"

        # ---- بدون پوزیشن: فقط خرید با تأیید روند صعودی ----
        uptrend = fast_ema > slow_sma and price > slow_sma * 1.0025

        if self.coin == 0.0:
            if self._last_buy_ts and time.time() - self._last_buy_ts < self.cooldown_sec:
                return "HOLD", "cooldown"
            if uptrend:
                return "BUY", "trend"
            return "HOLD", "no_trend"

        # ---- پوزیشن باز بدون تریگر استاپ/هدف: فروش فقط با شکست روند ----
        downtrend = fast_ema < slow_sma or price < slow_sma * 0.9975
        if downtrend:
            return "SELL", "treak_break"
        return "HOLD", "in_position"

    # ================= اجرای کاغذی =================
    def _buy(self, ask, reason):
        spend = self.balance * self.risk
        if spend < 3.0:
            return
        qty = spend / ask
        self.coin += qty
        self.entry = ask
        self.balance -= spend * (1.0 + self.fee)
        self._last_buy_ts = time.time()
        self._log("BUY", qty, ask, reason)

    def _sell(self, bid, reason):
        if self.coin <= 0.0:
            return
        qty = self.coin
        self.balance += qty * bid * (1.0 - self.fee)
        self.coin =  ​0.0
        self.entry =  ​0.0
        if self.balance >= self.initial:
            self.wins += 1
        else:
            self.losses += 1
        self._log("SELL", qty, bid, reason)

    def _log(self, side, qty, price, reason):
        self.trades.append({
            "ts": round(time.time(), 3),
            "side": side,
            "reason": reason,
            "qty": round(qty, 6),
            "price": round(price, 4),
            "balance": round(self.balance, 2),
        })
        log.info("AUTO %s (%s)  price=%.2f  balance=%.2f", side, reason, price, self.balance)
        self._save()

    # ================= چرخه زنده =================
    def _loop(self):
        while self.running:
            try:
                price, bid, ask, src = self.feed.tick()
                self._last_price = price
                self._last_src = src
                self.prices.append(price)
                if len(self.prices) > 1000:
                    self.prices = self.prices[-1000:]

                action, reason = self._decide(bid, ask)
                if action == "BUY":
                    self._buy(ask, reason)
                elif action == "SELL":
                    self._sell(bid, reason)
            except Exception as exc:
                log.error("پرش حلقه: %s", exc)
            time.sleep(self.tick_interval)

    # ================= کنترل =================
    def start(self):
        if self.running:
            return False
        self.running = True
        self.thread = threading.Thread(target=self._loop, name="autopilot", daemon=True)
        self.thread.start()
        log.info("AutoPilot started (paper) — chain: %s", self.feed.chain
        return True

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        log.info("AutoPilot stopped (paper)")
        return True

    # ================= وضعیت =================
    def status(self):
        unrealized = 0.0
        if self.coin:
            unrealized = (self._last_price - self.entry) * self.coin
        realized = self.balance - self.initial
        return {
            "running": self.running,
            "symbol": self.symbol,
            "feed": self._last_src,
            "price": round(self._last_price, 2),
            "balance": round(self.balance, 2),
            "coin": round(self.coin, 6),
            "entry": round(self.entry, 4),
            "realized_pnl": round(realized, 2),
            "unrealized_pnl": round(unrealized, 2),
            "total_pnl": round(realized + unrealized,  ​2),
            "wins": self.wins,
            "losses": self.losses,
            "trades": len(self.trades),
        }

    def _save(self):
        try:
            TRADES_FILE.write_text(
                json.dumps({"status":  ​self.status(), "trades":  ​self.trades},
                           ensure_ascii=False, indent=2))
        except Exception as exc:
            log.warning("ذخیره نشد: %s", exc)
