# -*- coding: utf-8 -*-
"""LiveFeed v3 — فید چندلایه با Failover خودکار.
اولویت: wallex → nobitex → binance → fake
اگه یک صرافی جواب نداد، خودکار میره سراغ بعدی؛ اگه همه قطع بودن، fake (سنتزی) جایگزین میشه تا ربات کرش نکنه.
"""
import json
import random
import time
import urllib.request


class LiveFeed:
    def __init__(self, source="auto", symbol="BTC/USDT", fallback_price=42000.0):
        self.symbol = symbol
        self.price = float(fallback_price)
        self.bid = self.price
        self.ask = self.price
        self.last_src = "?"
        self._cache_until = 0.0
        if source == "auto":
            self.chain = ["wallex", "nobitex", "binance", "fake"]
        elif source == "fake":
            self.chain = ["fake"]
        else:
            self.chain = [source, "fake"]
        self._chain_idx = 0

    # ================= گرفتن یه تیک =================
    def tick(self):
        now = time.time()
        if now < self._cache_until:
            return (self.price, self.bid, self.ask, self.last_src + ":cache")

        for i in range(len(self.chain)):
            idx = (self._chain_idx + i) % len(self.chain)
            src = self.chain[idx]
            updater = getattr(self, "_update_" + src, None)
            if updater is None:
                continue
            try:
                updater()
                self.last_src = src
                self._chain_idx = idx
                self._cache_until = now + 2.0
                return (self.price, self.bid, self.ask, src)
            except Exception:
                continue   # این صرافی جواب نداد → برو بعدی

        # همهی صرافیها قطع بودن: قیمت قبلی، بدون کرش
        self._chain_idx = (self._chain_idx + 1) % len(self.chain)
        self._cache_until = now + 1.0
        return (self.price, self.bid, self.ask, self.last_src + ":stale")

    # ================= منابع داده (همه self.price/bid/ask رو ست میکنن) =================
    def _update_fake(self):
        self.price = max(1.0, self.price * random.uniform(0.997, 1.0035))
        spread = self.price * 0.001
        self.bid = self.price - spread
        self.ask = self.price + spread

    def _update_wallex(self):
        sym = self.symbol.replace("/", "")
        data = self._get_json("https://api.wallex.ir/v1/markets")
        stats = data["result"]["symbols"][sym]["stats"]
        self.bid = float(stats["bidPrice"])
        self.ask = float(stats["askPrice"])
        self.price = float(stats.get("lastPrice") or (self.bid + self.ask) / 2.0

    def _update_nobitex(self):
        base, quote = self.symbol.split("/")
        url = ("https://api.nobitex.ir/v2/trade?"
               "srcCurrency=%s&dstCurrency=%s" % (base.lower(), quote.lower()))
        data = self._get_json(url)
        stats = data["stats"]["%s-%s" % (base.lower(), quote.lower())]
        self.ask = float(stats["bestAsk"])
        self.bid = float(stats["bestBid"])
        last = float(stats.get("latest", 0) or 0)
        self.price = last or (self.bid + self.ask) / 2.0

    def _update_binance(self):
        sym = self.symbol.replace("/", "")
        data = self._get_json("https://api.binance.com/api/v3/ticker/bookTicker?symbol=" + sym)
        self.bid = float(data["bidPrice"])
        self.ask = float(data["askPrice"])
        self.price = (self.bid + self.ask) / 2.0

    def _get_json(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "AtriaTrade/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))

    # ================= نمایش قشنگ ترمینال =================
    @staticmethod
    def pretty_status(st):
        sep = "─" * 42
        lines = ["🤖  ** ربات متوقف است **"] if not st.get("running", False) else ["🤖  ** ربات فعال است **"]
        lines.append(sep)
        lines.append("💰  بالانس:         %s $" % str(st.get("balance", "?")))
        lines.append("🪙  سکه:            %s" % str(st.get("coin", "?")))
        lines.append("💵  قیمت لحظه:      %s $" % str(st.get("price", "?")))
        pnl_str = ("+" if float(st.get("total_pnl", 0)) >= 0 else "") + str(st.get("total_pnl", "?"))) + " $"
        lines.append("📊  سود/زیان کل:     %s" % pnl_str)
        lines.append("📈  برد:            %s" % str(st.get("wins", "?")))
        lines.append("📉  باخت:           %s" % str(st.get("losses", "?")))
        lines.append("🔄  معاملات:        %s" % str(st.get("trades", "?")))
        lines.append(sep)
        lines.append("⏱  منبع:   %s" % st.get("feed", "?"))
        return "\n".join(lines)
