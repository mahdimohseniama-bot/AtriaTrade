"""
AtriaTrade — Diagnostic: Profit Flow in TradingEngine (READ-ONLY)
Simulates the CURRENT behavior of TradingEngine.process_tick SELL path
with the real fallback chain:
  add_to_vault -> process_trade_profit -> process_trade_pnl -> deposit -> record_profit
NO core files are modified. This is a pure diagnostic.
"""
from dataclasses import dataclass, field

# ---------- Lightweight replicas (exact logic of real modules) ----------

class PortfolioManager:
    def __init__(self, initial_cash=1000.0):
        self.cash = float(initial_cash)
        self.realized_pnl = 0.0
        self.positions = {}          # symbol -> {"qty": float, "avg_price": float}

    def record_buy(self, symbol, qty, price, fee=0.0):
        pos = self.positions.setdefault(symbol, {"qty": 0.0, "avg_price": 0.0})
        total_cost = pos["avg_price"] * pos["qty"] + price * qty
        pos["qty"] += qty
        pos["avg_price"] = total_cost / pos["qty"] if pos["qty"] > 0 else 0.0
        self.cash -= qty * price + fee
        return {"status": "FILLED", "action": "BUY", "symbol": symbol,
                "quantity": qty, "price": price, "cash": self.cash}

    def record_sell(self, symbol, qty, price, fee=0.0):
        pos = self.positions.get(symbol, {"qty": 0.0, "avg_price": 0.0})
        if qty > pos["qty"]:
            qty = pos["qty"]
        pnl = (price - pos["avg_price"]) * qty - fee
        self.cash += qty * price - fee
        pos["qty"] -= qty
        if pos["qty"] <= 0:
            self.positions.pop(symbol, None)
        self.realized_pnl += pnl
        return {"status": "FILLED", "action": "SELL", "symbol": symbol,
                "quantity": qty, "price": price, "fee": fee,
                "realized_pnl": pnl, "cash": self.cash}


class ProfitReserveManager:
    """Replica with BOTH models — exposing the conflict:
    - add_to_vault: creates ad-hoc `vault_balance`, bypasses ratio entirely
    - process_trade_profit: uses reserve_ratio (currently DEAD path in engine)
    """
    def __init__(self, reserve_ratio=0.5):
        self.reserve_ratio = reserve_ratio
        self.total_reserved_profit = 0.0
        self.reserve_history = []

    def process_trade_profit(self, profit_amount, trade_id=None):
        reserved = profit_amount * self.reserve_ratio
        reinvest = profit_amount - reserved
        self.total_reserved_profit += reserved
        self.reserve_history.append({"trade_id": trade_id,
                                     "reserved": reserved, "reinvested": reinvest})
        return {"reserved_amount": reserved, "reinvest_amount": reinvest,
                "total_reserved": self.total_reserved_profit}

    # --- compatibility patch (exact real behavior: wins over ratio model) ---
    def add_to_vault(self, amount):
        if not hasattr(self, "vault_balance"):
            self.vault_balance = 0.0
        self.vault_balance += amount


class TradingEngine:
    """Replica of the SELL path in real process_tick (L88-149)."""
    def __init__(self, portfolio_manager=None, profit_reserve_manager=None):
        self.portfolio_manager = portfolio_manager
        self.profit_reserve_manager = profit_reserve_manager
        self._entry_prices = {}

    def process_tick(self, tick):
        signal = tick.get("signal")
        symbol = tick.get("symbol")
        price = float(tick.get("price", 0))

        if signal == "BUY":
            qty = float(tick.get("quantity", self.portfolio_manager.cash * 0.5 / price))
            self.portfolio_manager.record_buy(symbol, qty, price)
            self._entry_prices[symbol] = price
            return {"status": "FILLED", "action": "BUY", "symbol": symbol, "price": price}

        if signal == "SELL":
            pos = self.portfolio_manager.positions.get(symbol)
            current_qty = pos["qty"] if pos else 0.0
            if current_qty <= 0:
                return None  # coverage gap: SELL without prior BUY
            qty_to_sell = min(float(tick.get("quantity", current_qty)), current_qty)
            sell_res = self.portfolio_manager.record_sell(symbol, qty_to_sell, price)

            # --- realized pnl extraction (real fallback chain) ---
            realized_pnl = sell_res.get("realized_pnl", 0.0)
            if realized_pnl == 0.0 and symbol in self._entry_prices:
                realized_pnl = (price - self._entry_prices[symbol]) * qty_to_sell

            # --- profit hand-off (real fallback chain L125-139) ---
            reserve_path = None
            if realized_pnl > 0 and self.profit_reserve_manager is not None:
                r = self.profit_reserve_manager
                if hasattr(r, "add_to_vault"):
                    r.add_to_vault(realized_pnl)
                    reserve_path = "add_to_vault"
                elif hasattr(r, "process_trade_profit"):
                    r.process_trade_profit(realized_pnl)
                    reserve_path = "process_trade_profit"
            return {"status": "FILLED", "action": "SELL", "symbol": symbol,
                    "price": price, "realized_pnl": realized_pnl,
                    "reserve_path": reserve_path}
        return None


# ---------- Diagnostic scenario ----------
def snapshot(engine, label):
    p, r = engine.portfolio_manager, engine.profit_reserve_manager
    print(f"\n--- {label} ---")
    print(f"  portfolio.cash               = {p.cash:.2f}")
    print(f"  portfolio.realized_pnl       = {p.realized_pnl:.2f}")
    print(f"  reserve.total_reserved_profit= {r.total_reserved_profit:.2f}")
    print(f"  reserve.vault_balance        = {getattr(r, 'vault_balance', 'MISSING')}")
    print(f"  reserve.reserve_history len  = {len(r.reserve_history)} (ratio model usage)")

def main():
    pm = PortfolioManager(initial_cash=1000.0)
    prm = ProfitReserveManager(reserve_ratio=0.5)
    eng = TradingEngine(portfolio_manager=pm, profit_reserve_manager=prm)

    print("=" * 60)
    print("AtriaTrade Profit-Flow Diagnostic (paper, read-only)")
    print("=" * 60)

    # Trade A: BUY 2 @100 -> SELL 2 @150  (expected pnl=+100... note avg_price path)
    print("\n[A] BUY BTC 2@100")
    eng.process_tick({"symbol": "BTC", "price": 100.0, "signal": "BUY", "quantity": 2.0})
    print("[A] SELL BTC 2@150  -> expect reserve_path='add_to_vault', total_reserved stays 0")
    res = eng.process_tick({"symbol": "BTC", "price": 150.0, "signal": "SELL", "quantity": 2.0})
    print(f"    result: {res}")
    snapshot(eng, "after Trade A")

    # Trade B: SELL without BUY  (coverage gap)
    print("\n[B] SELL ETH without prior BUY -> expect None (coverage gap)")
    res = eng.process_tick({"symbol": "ETH", "price": 50.0, "signal": "SELL", "quantity": 1.0})
    print(f"    result: {res}   <-- GAP#3 confirmed if None")
    snapshot(eng, "after Trade B")

    # Trade C: BUY 1@100 -> SELL 1@60 (loss)
    print("\n[C] BUY SOL 1@100")
    eng.process_tick({"symbol": "SOL", "price": 100.0, "signal": "BUY", "quantity": 1.0})
    print("[C] SELL SOL 1@60 -> expect realized_pnl=-40, reserve UNTOUCHED (loss invisible to reserve)")
    res = eng.process_tick({"symbol": "SOL", "price": 60.0, "signal": "SELL", "quantity": 1.0})
    print(f"    result: {res}   <-- GAP#1 confirmed if reserve_path=None on loss")
    snapshot(eng, "after Trade C (FINAL)")

    print("\n" + "=" * 60)
    print("VERDICT: if vault_balance != 0 while total_reserved_profit == 0,")
    print("the ratio model is DEAD and add_to_vault bypasses ProfitAllocator logic.")
    print("=" * 60)

if __name__ == "__main__":
    main()
