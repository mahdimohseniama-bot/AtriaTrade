#!/usr/bin/env python3
import time
import json
import os
import uuid
import requests
from datetime import datetime

from src.adapters.paper_factory import PaperExchangeFactory
from src.core.smc_composite_engine import SMCCompositeEngine


def now_iso():
    return datetime.now().isoformat()


class TradeLogger:
    """Append-only JSON journal (list of events)."""
    LOG_FILE = "trade_journal.json"

    @classmethod
    def append(cls, record: dict):
        data = []
        if os.path.exists(cls.LOG_FILE):
            try:
                with open(cls.LOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except Exception:
                data = []
        data.append(record)
        with open(cls.LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"📁 [JOURNAL] saved -> {cls.LOG_FILE}")


class WallexPublicDataFetcher:
    BASE_URL = "https://api.wallex.ir"

    @classmethod
    def fetch_candles(cls, symbol="BTCUSDT", resolution="60", limit=60):
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (limit * int(resolution) * 60)
            url = f"{cls.BASE_URL}/v1/udf/history"
            params = {"symbol": symbol, "resolution": resolution, "from": from_ts, "to": to_ts}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("s") != "ok" or not data.get("t"):
                return []

            candles = []
            for t, o, h, l, c, v in zip(data["t"], data["o"], data["h"], data["l"], data["c"], data["v"]):
                candles.append(
                    {
                        "timestamp": int(t) * 1000,
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c),
                        "volume": float(v),
                    }
                )
            return candles
        except Exception as e:
            print(f"⚠️ [Data Warning] {e}")
            return []


class PositionManager:
    def __init__(self, risk_reward_ratio=2.0, trailing_step_pct=0.006):
        self.active_position = None
        self.rr = float(risk_reward_ratio)
        self.trailing_step = float(trailing_step_pct)

    def has_position(self):
        return self.active_position is not None

    def snapshot(self):
        """Return a JSON-safe snapshot of current position (or None)."""
        if not self.active_position:
            return None
        return dict(self.active_position)

    def open_position(self, side, entry_price, qty, stop_loss, symbol, adapter):
        side = side.upper()
        entry_price = float(entry_price)
        stop_loss = float(stop_loss)
        qty = float(qty)

        risk = abs(entry_price - stop_loss)
        if risk <= 0:
            risk = entry_price * 0.01
        take_profit = entry_price + (risk * self.rr) if side == "BUY" else entry_price - (risk * self.rr)

        trade_id = str(uuid.uuid4())
        self.active_position = {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": side,
            "entry_time": now_iso(),
            "entry_price": entry_price,
            "qty": qty,
            "stop_loss": stop_loss,
            "take_profit": float(take_profit),
            "max_favorable_price": entry_price,  # BUY: max, SELL: min
        }

        print("\n" + "=" * 60)
        print(f"🎯 [NEW POSITION] {side} | Qty: {qty:.6f}")
        print(f"   Entry: ${entry_price:,.2f} | SL: ${stop_loss:,.2f} | TP: ${take_profit:,.2f}")
        print("=" * 60 + "\n")

        # Journal ENTRY immediately
        TradeLogger.append(
            {
                "event": "ENTRY",
                "time": now_iso(),
                "trade_id": trade_id,
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "quantity": qty,
                "stop_loss": stop_loss,
                "take_profit": float(take_profit),
                "usdt_balance": round(float(adapter.get_balance("usdt") or 0.0), 6),
                "btc_balance": round(float(adapter.get_balance("btc") or 0.0), 10),
            }
        )

    def update_trailing(self, current_price: float):
        pos = self.active_position
        if not pos:
            return

        side = pos["side"]
        sl = pos["stop_loss"]

        if side == "BUY":
            if current_price > pos["max_favorable_price"]:
                pos["max_favorable_price"] = current_price
                new_sl = max(sl, current_price * (1 - self.trailing_step))
                if new_sl > sl:
                    pos["stop_loss"] = float(new_sl)

        elif side == "SELL":
            if current_price < pos["max_favorable_price"]:
                pos["max_favorable_price"] = current_price
                new_sl = min(sl, current_price * (1 + self.trailing_step))
                if new_sl < sl:
                    pos["stop_loss"] = float(new_sl)

    def check_exit(self, current_price: float):
        pos = self.active_position
        if not pos:
            return None

        side = pos["side"]
        entry = pos["entry_price"]
        sl = pos["stop_loss"]
        tp = pos["take_profit"]

        if (side == "BUY" and current_price >= tp) or (side == "SELL" and current_price <= tp):
            pnl_pct = ((tp - entry) / entry) * 100 if side == "BUY" else ((entry - tp) / entry) * 100
            return ("TAKE_PROFIT", float(pnl_pct))

        if (side == "BUY" and current_price <= sl) or (side == "SELL" and current_price >= sl):
            pnl_pct = ((sl - entry) / entry) * 100 if side == "BUY" else ((entry - sl) / entry) * 100
            return ("STOP_LOSS", float(pnl_pct))

        return None

    def close_and_journal(self, adapter, symbol: str, exit_price: float, reason: str, pnl_pct: float):
        pos = self.active_position
        if not pos:
            return

        # Close to flat in paper (best-effort)
        if pos["side"] == "BUY":
            btc_bal = float(adapter.get_balance("btc") or 0.0)
            if btc_bal > 1e-10:
                adapter.place_order(symbol, "sell", "market", btc_bal)

        elif pos["side"] == "SELL":
            usdt_bal = float(adapter.get_balance("usdt") or 0.0)
            if usdt_bal > 10:
                buy_qty = min(pos["qty"], (usdt_bal * 0.98) / max(pos["entry_price"], 1e-9))
                if buy_qty > 1e-10:
                    adapter.place_order(symbol, "buy", "market", buy_qty)

        TradeLogger.append(
            {
                "event": "EXIT",
                "time": now_iso(),
                "trade_id": pos["trade_id"],
                "symbol": symbol,
                "side": pos["side"],
                "entry_time": pos["entry_time"],
                "exit_price": float(exit_price),
                "exit_reason": reason,
                "pnl_percentage": round(float(pnl_pct), 6),
                "final_usdt_balance": round(float(adapter.get_balance("usdt") or 0.0), 6),
                "final_btc_balance": round(float(adapter.get_balance("btc") or 0.0), 10),
            }
        )
        self.active_position = None


def run():
    symbol = "BTCUSDT"
    resolution = "60"  # minutes
    risk_pct = 0.20
    min_score = 25.0

    print("=" * 65)
    print("🚀 [AtriaTrade] Wallex Live Data + Paper Trading + Journal")
    print(f"📊 Symbol: {symbol} | TF: {resolution}m | EntryScore>={min_score} | Risk: {int(risk_pct*100)}%")
    print("=" * 65)

    adapter = PaperExchangeFactory.create_adapter("wallex", {"usdt": 1000.0, "btc": 0.0})
    engine = SMCCompositeEngine(min_confidence_score=min_score)
    pos_mgr = PositionManager(risk_reward_ratio=2.0, trailing_step_pct=0.006)

    poll = 0
    try:
        while True:
            poll += 1

            candles = WallexPublicDataFetcher.fetch_candles(symbol=symbol, resolution=resolution, limit=60)
            if len(candles) < 25:
                print("⏳ waiting for enough candles ...")
                time.sleep(10)
                continue

            latest = candles[-1]
            current_price = float(latest["close"])
            adapter.set_market_price(symbol, current_price)

            window = candles[-20:]
            range_high = max(c["high"] for c in window)
            range_low = min(c["low"] for c in window)
            swing_low = min(c["low"] for c in window[-5:])
            swing_high = max(c["high"] for c in window[-5:])

            body = abs(latest["close"] - latest["open"])
            rng = max(range_high - range_low, 1e-9)
            fvg_detected = body > (rng * 0.10)
            fvg_direction = "BUY" if latest["close"] > latest["open"] else "SELL"

            smc = engine.generate_signal(
                symbol=symbol,
                current_price=current_price,
                range_high=range_high,
                range_low=range_low,
                fvg_detected=fvg_detected,
                fvg_direction=fvg_direction,
            )

            ts = datetime.now().strftime("%H:%M:%S")

            if pos_mgr.has_position():
                pos_mgr.update_trailing(current_price)
                pos = pos_mgr.active_position

                pnl_live = (
                    ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
                    if pos["side"] == "BUY"
                    else ((pos["entry_price"] - current_price) / pos["entry_price"]) * 100
                )
                print(
                    f"[{ts}] #{poll} | POS:{pos['side']} | Cur:{current_price:,.1f} | "
                    f"PnL:{pnl_live:+.2f}% | SL:{pos['stop_loss']:,.1f} | TP:{pos['take_profit']:,.1f}"
                )

                exit_check = pos_mgr.check_exit(current_price)
                if exit_check:
                    reason, pnl_pct = exit_check
                    print(f"\n🚪 [EXIT] {reason} | pnl={pnl_pct:+.2f}% | exit={current_price:,.2f}\n")
                    pos_mgr.close_and_journal(adapter, symbol, current_price, reason, pnl_pct)

            else:
                print(f"[{ts}] #{poll} | Price:{current_price:,.2f} | Score:{smc.score:.1f} | Dir:{smc.direction} | Conf:{smc.confidence}")

                usdt_bal = float(adapter.get_balance("usdt") or 0.0)
                if smc.direction in ("BUY", "SELL") and float(smc.score) >= min_score and usdt_bal >= 50:
                    qty = (usdt_bal * risk_pct) / max(current_price, 1e-9)
                    sl = (swing_low * 0.998) if smc.direction == "BUY" else (swing_high * 1.002)
                    adapter.place_order(symbol, smc.direction.lower(), "market", qty)
                    pos_mgr.open_position(smc.direction, current_price, qty, sl, symbol, adapter)

            time.sleep(20)

    except KeyboardInterrupt:
        print("\n🛑 stopped by user.")
        snap = pos_mgr.snapshot()
        if snap:
            TradeLogger.append(
                {
                    "event": "STOPPED_WITH_OPEN_POSITION",
                    "time": now_iso(),
                    "trade_id": snap.get("trade_id"),
                    "symbol": snap.get("symbol"),
                    "side": snap.get("side"),
                    "entry_time": snap.get("entry_time"),
                    "entry_price": snap.get("entry_price"),
                    "current_price": None,  # not guaranteed at stop moment
                    "stop_loss": snap.get("stop_loss"),
                    "take_profit": snap.get("take_profit"),
                    "quantity": snap.get("qty"),
                    "usdt_balance": round(float(adapter.get_balance("usdt") or 0.0), 6),
                    "btc_balance": round(float(adapter.get_balance("btc") or 0.0), 10),
                }
            )


if __name__ == "__main__":
    run()
