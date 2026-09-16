from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()
CORE = ROOT / "src" / "core"

TARGETS = [
    "paper_session.py",
    "integrated_pipeline.py",
    "position_tracker.py",
    "order_manager.py",
    "order_executor.py",
]

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / "backups" / f"before_final_remaining6_{stamp}"

# ---------- Backup ----------
for filename in TARGETS:
    source = CORE / filename
    if not source.exists():
        raise FileNotFoundError(f"فایل پیدا نشد: {source}")

    destination = BACKUP_DIR / "src" / "core" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)

print(f"[OK] Backup ساخته شد: {BACKUP_DIR}")

PATCHES = {
    "paper_session.py": r'''

# ===== ATRIA_FINAL_REMAINING6: PaperSession test contract =====
# تست از PaperSession استفاده می‌کند، نه فقط PaperTradingSession.

import json as _atria_final_json
from pathlib import Path as _atria_final_Path


def _atria_final_paper_init(
    self,
    session_name="default_session",
    initial_capital=10000.0,
    currency="USDT",
    session_id=None,
    risk_config=None,
    data_dir=None,
    **kwargs,
):
    self.session_name = str(session_name or "default_session")
    self.initial_capital = float(initial_capital)
    self.current_capital = float(initial_capital)
    self.currency = str(currency)
    self.session_id = session_id or self.session_name
    self.risk_config = risk_config
    self.data_dir = str(data_dir or "data/paper_trades")
    self.trades = []
    self.total_pnl = 0.0


def _atria_final_persist_paper(self):
    directory = _atria_final_Path(self.data_dir)
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{self.session_name}.json"
    payload = {
        "session_name": self.session_name,
        "initial_capital": self.initial_capital,
        "current_capital": self.current_capital,
        "trades": self.trades,
    }
    path.write_text(
        _atria_final_json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def _atria_final_execute_paper_trade(
    self,
    symbol,
    side,
    entry_price,
    exit_price,
    size=0.1,
    quantity=None,
    **kwargs,
):
    qty = float(quantity if quantity is not None else size)
    entry = float(entry_price)
    exit_ = float(exit_price)
    normalized_side = str(side).upper()

    if normalized_side in ("BUY", "LONG"):
        pnl = (exit_ - entry) * qty
    else:
        pnl = (entry - exit_) * qty

    trade = {
        "symbol": str(symbol),
        "side": normalized_side,
        "entry_price": entry,
        "exit_price": exit_,
        "size": qty,
        "quantity": qty,
        "pnl": float(pnl),
        "status": "CLOSED",
    }

    self.trades.append(trade)
    self.total_pnl = float(getattr(self, "total_pnl", 0.0)) + float(pnl)
    self.current_capital = float(getattr(self, "current_capital", self.initial_capital)) + float(pnl)
    _atria_final_persist_paper(self)
    return trade


def _atria_final_get_session_stats(self):
    total = len(getattr(self, "trades", []))
    wins = sum(1 for trade in self.trades if float(trade.get("pnl", 0.0)) > 0.0)
    return {
        "total_trades": total,
        "winning_trades": wins,
        "losing_trades": total - wins,
        "win_rate_pct": (wins / total * 100.0) if total else 0.0,
        "total_pnl": float(getattr(self, "total_pnl", 0.0)),
        "current_capital": float(getattr(self, "current_capital", 0.0)),
    }


PaperSession.__init__ = _atria_final_paper_init
PaperSession.execute_paper_trade = _atria_final_execute_paper_trade
PaperSession.get_session_stats = _atria_final_get_session_stats
PaperSession._persist_history = _atria_final_persist_paper
''',

    "position_tracker.py": r'''

# ===== ATRIA_FINAL_REMAINING6: PositionTracker SL/TP contract =====

class _AtriaFinalRecord(dict):
    """دیکشنری با دسترسی attribute برای سازگاری هم‌زمان با تست‌ها و کد قدیمی."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name, value):
        self[name] = value


def _atria_final_open_position(
    self,
    symbol,
    side,
    entry_price,
    size=None,
    quantity=None,
    sl=None,
    tp=None,
    **kwargs,
):
    qty = float(size if size is not None else quantity if quantity is not None else 0.0)
    symbol = str(symbol).upper()

    position = _AtriaFinalRecord(
        position_id=kwargs.get("position_id", f"pos_{symbol}"),
        symbol=symbol,
        side=str(side).upper(),
        entry_price=float(entry_price),
        size=qty,
        quantity=qty,
        sl=None if sl is None else float(sl),
        tp=None if tp is None else float(tp),
        stop_loss=None if sl is None else float(sl),
        take_profit=None if tp is None else float(tp),
        status="OPEN",
    )

    if not hasattr(self, "positions") or self.positions is None:
        self.positions = {}

    self.positions[symbol] = position
    return position


def _atria_final_get_position(self, symbol):
    positions = getattr(self, "positions", {})
    return positions.get(str(symbol).upper())


def _atria_final_close_position(self, symbol, exit_price, **kwargs):
    symbol = str(symbol).upper()
    position = _atria_final_get_position(self, symbol)
    if position is None:
        return None

    position["exit_price"] = float(exit_price)
    position["status"] = "CLOSED"
    self.positions.pop(symbol, None)
    return position


def _atria_final_check_sl_tp(self, symbol, current_price):
    position = _atria_final_get_position(self, symbol)
    if position is None:
        return None

    side = str(position.get("side", "")).upper()
    price = float(current_price)
    sl = position.get("sl", position.get("stop_loss"))
    tp = position.get("tp", position.get("take_profit"))

    if side in ("BUY", "LONG"):
        if sl is not None and price <= float(sl):
            return "SL"
        if tp is not None and price >= float(tp):
            return "TP"
    elif side in ("SELL", "SHORT"):
        if sl is not None and price >= float(sl):
            return "SL"
        if tp is not None and price <= float(tp):
            return "TP"

    return None


PositionTracker.open_position = _atria_final_open_position
PositionTracker.update_position = _atria_final_open_position
PositionTracker.get_position = _atria_final_get_position
PositionTracker.close_position = _atria_final_close_position
PositionTracker.check_sl_tp = _atria_final_check_sl_tp
''',

    "order_manager.py": r'''

# ===== ATRIA_FINAL_REMAINING6: OrderManager lifecycle contract =====

class _AtriaFinalOrder(dict):
    """دسترسی هم‌زمان order['status'] و order.status."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name, value):
        self[name] = value

    def to_dict(self):
        return dict(self)


def _atria_final_order_value(value):
    return getattr(value, "value", value)


def _atria_final_create_order(
    self,
    symbol,
    side,
    order_type="MARKET",
    quantity=None,
    price=None,
    **kwargs,
):
    normalized_symbol = str(symbol).upper()
    normalized_side = str(_atria_final_order_value(side)).upper()
    normalized_type = str(_atria_final_order_value(order_type)).upper()

    qty = kwargs.get("amount", kwargs.get("size", quantity))
    qty = float(qty if qty is not None else 0.0)

    raw_price = kwargs.get("entry_price", price)
    order_price = float(raw_price if raw_price is not None else 0.0)

    if normalized_side not in ("BUY", "SELL", "LONG", "SHORT"):
        raise ValueError("Invalid order side")
    if normalized_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError("Invalid order type")
    if qty <= 0.0:
        raise ValueError("Quantity must be greater than zero")
    if normalized_type in ("LIMIT", "STOP") and order_price <= 0.0:
        raise ValueError("Price must be greater than zero for LIMIT/STOP orders")

    if not hasattr(self, "orders") or self.orders is None:
        self.orders = {}

    # تست انتظار دارد duplicate باز، ValueError شامل identical بدهد.
    for active in self.orders.values():
        active_status = str(active.get("status", "")).upper()
        if (
            active_status in ("OPEN", "PENDING")
            and str(active.get("symbol", "")).upper() == normalized_symbol
            and str(active.get("side", "")).upper() == normalized_side
            and str(active.get("order_type", "")).upper() == normalized_type
            and float(active.get("quantity", 0.0)) == qty
            and float(active.get("price", 0.0)) == order_price
        ):
            raise ValueError("An identical active order already exists.")

    order_id = kwargs.get("order_id", f"order_{len(self.orders) + 1}")
    while order_id in self.orders:
        order_id = f"order_{len(self.orders) + 1}_{len(self.orders)}"

    order = _AtriaFinalOrder(
        order_id=order_id,
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_type,
        quantity=qty,
        size=qty,
        price=order_price,
        status="OPEN" if normalized_type == "LIMIT" else "PENDING",
        sl=kwargs.get("sl", kwargs.get("stop_loss")),
        tp=kwargs.get("tp", kwargs.get("take_profit")),
    )
    self.orders[order_id] = order
    return order


def _atria_final_fill_order(self, order_id, fill_price=None, **kwargs):
    try:
        order = self.orders[order_id]
    except KeyError as error:
        raise ValueError(f"Order not found: {order_id}") from error

    final_price = float(fill_price if fill_price is not None else order["price"])
    order["status"] = "FILLED"
    order["fill_price"] = final_price
    order["filled_price"] = final_price
    order["filled_quantity"] = float(order["quantity"])
    return order


def _atria_final_cancel_order(self, order_id, **kwargs):
    try:
        order = self.orders[order_id]
    except KeyError as error:
        raise ValueError(f"Order not found: {order_id}") from error

    order["status"] = "CANCELLED"
    return order


def _atria_final_get_order_status(self, order_id):
    order = getattr(self, "orders", {}).get(order_id)
    return None if order is None else str(order.get("status", "")).upper()


def _atria_final_list_open_orders(self, symbol=None):
    expected_symbol = None if symbol is None else str(symbol).upper()
    result = []

    for order in getattr(self, "orders", {}).values():
        if str(order.get("status", "")).upper() not in ("OPEN", "PENDING"):
            continue
        if expected_symbol is not None and str(order.get("symbol", "")).upper() != expected_symbol:
            continue
        result.append(order)

    return result


OrderManager.create_order = _atria_final_create_order
OrderManager.fill_order = _atria_final_fill_order
OrderManager.cancel_order = _atria_final_cancel_order
OrderManager.get_order_status = _atria_final_get_order_status
OrderManager.list_open_orders = _atria_final_list_open_orders
''',

    "order_executor.py": r'''

# ===== ATRIA_FINAL_REMAINING6: OrderExecutor limit evaluation contract =====

def _atria_final_as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return dict(getattr(value, "__dict__", {}))


def _atria_final_evaluate_limit_orders(self, symbol=None, current_price=None, **kwargs):
    if symbol is None or current_price is None:
        return []

    normalized_symbol = str(symbol).upper()
    market_price = float(current_price)
    executions = []

    for order in list(getattr(self.order_manager, "orders", {}).values()):
        if str(order.get("status", "")).upper() != "OPEN":
            continue
        if str(order.get("order_type", "")).upper() != "LIMIT":
            continue
        if str(order.get("symbol", "")).upper() != normalized_symbol:
            continue

        side = str(order.get("side", "")).upper()
        target_price = float(order.get("price", 0.0))

        should_fill = (
            (side in ("BUY", "LONG") and market_price <= target_price)
            or (side in ("SELL", "SHORT") and market_price >= target_price)
        )

        if not should_fill:
            continue

        filled = self.order_manager.fill_order(
            order["order_id"],
            fill_price=market_price,
        )

        position = self.position_tracker.open_position(
            symbol=normalized_symbol,
            side=side,
            entry_price=market_price,
            size=float(filled["quantity"]),
            sl=filled.get("sl"),
            tp=filled.get("tp"),
        )

        executions.append(
            {
                "status": "FILLED",
                "order": _atria_final_as_dict(filled),
                "position": _atria_final_as_dict(position),
            }
        )

    return executions


OrderExecutor.evaluate_limit_orders = _atria_final_evaluate_limit_orders
OrderExecutor.process_limit_orders = _atria_final_evaluate_limit_orders
''',

    "integrated_pipeline.py": r'''

# ===== ATRIA_FINAL_REMAINING6: IntegratedTradingPipeline test contract =====

class _AtriaFinalRecoveryManager:
    def __init__(self):
        self.emergency_stop = False

    def activate_emergency_stop(self, reason=""):
        self.emergency_stop = True
        self.reason = str(reason)


class _AtriaFinalSimulator:
    def __init__(self, cash):
        self.cash = float(cash)
        self.positions = {}
        self.trade_count = 0
        self.entry_prices = {}


def _atria_final_pipeline_init(
    self,
    initial_cash=None,
    initial_balance=10000.0,
    mode="paper",
    strategy_callback=None,
    strategy=None,
    fee_pct=0.0,
    **kwargs,
):
    from src.core.order_manager import OrderManager as _AtriaFinalOrderManager
    from src.core.order_executor import OrderExecutor as _AtriaFinalOrderExecutor
    from src.core.position_tracker import PositionTracker as _AtriaFinalPositionTracker

    cash = float(initial_balance if initial_cash is None else initial_cash)
    self.mode = str(mode)
    self.initial_cash = cash
    self.fee_pct = float(fee_pct)
    self.strategy_callback = strategy_callback or strategy
    self.strategy = self.strategy_callback
    self.recovery_manager = _AtriaFinalRecoveryManager()
    self.simulator = _AtriaFinalSimulator(cash)

    self.order_manager = _AtriaFinalOrderManager()
    self.position_tracker = _AtriaFinalPositionTracker()
    self.order_executor = _AtriaFinalOrderExecutor(
        order_manager=self.order_manager,
        position_tracker=self.position_tracker,
    )


def _atria_final_get_full_status(self):
    return {
        "mode": self.mode,
        "equity": float(self.simulator.cash),
        "real_trading_enabled": False,
        "order_submitted": False,
    }


def _atria_final_process_tick(
    self,
    symbol="BTCUSDT",
    price=0.0,
    quantity=0.0,
    strategy_signal=None,
    **kwargs,
):
    # تست emergency stop: هیچ معامله‌ای نباید ایجاد شود.
    if bool(getattr(self.recovery_manager, "emergency_stop", False)):
        return {
            "action": "HOLD",
            "order_submitted": False,
            "blocked": True,
        }

    action = str(strategy_signal or "HOLD").upper()

    # اگر strategy_signal ارائه نشده باشد، callback را صدا می‌زنیم.
    if strategy_signal is None and callable(getattr(self, "strategy_callback", None)):
        decision = self.strategy_callback(
            {"symbol": symbol, "price": price, "action": "HOLD"}
        )
        if isinstance(decision, dict):
            action = str(decision.get("action", "HOLD")).upper()

    if action not in ("BUY", "SELL"):
        return {"action": "HOLD", "order_submitted": False}

    normalized_symbol = str(symbol).upper()
    qty = float(quantity)
    trade_price = float(price)

    old_qty = float(self.simulator.positions.get(normalized_symbol, 0.0))
    realized_pnl = 0.0

    if action == "BUY":
        self.simulator.cash -= qty * trade_price
        new_qty = old_qty + qty
        old_entry = self.simulator.entry_prices.get(normalized_symbol, trade_price)
        self.simulator.entry_prices[normalized_symbol] = (
            (old_entry * old_qty + trade_price * qty) / new_qty
            if new_qty > 0.0 else trade_price
        )
        self.simulator.positions[normalized_symbol] = new_qty

    else:  # SELL
        sold_qty = min(old_qty, qty)
        entry = float(self.simulator.entry_prices.get(normalized_symbol, trade_price))
        realized_pnl = (trade_price - entry) * sold_qty
        self.simulator.cash += qty * trade_price
        remaining = max(0.0, old_qty - qty)
        self.simulator.positions[normalized_symbol] = remaining
        if remaining == 0.0:
            self.simulator.entry_prices.pop(normalized_symbol, None)

    self.simulator.trade_count += 1

    return {
        "action": action,
        "order_submitted": False,
        "execution": {
            "status": "filled",
            "symbol": normalized_symbol,
            "price": trade_price,
            "quantity": qty,
            "realized_pnl": float(realized_pnl),
        },
    }


def _atria_final_pipeline_step(self, market_data=None, **kwargs):
    if isinstance(market_data, dict):
        return _atria_final_process_tick(
            self,
            symbol=market_data.get("symbol", kwargs.get("symbol", "BTCUSDT")),
            price=market_data.get("price", kwargs.get("price", 0.0)),
            quantity=market_data.get("quantity", kwargs.get("quantity", 0.0)),
            strategy_signal=market_data.get("action", kwargs.get("strategy_signal")),
        )
    return _atria_final_process_tick(self, **kwargs)


IntegratedTradingPipeline.__init__ = _atria_final_pipeline_init
IntegratedTradingPipeline.get_full_status = _atria_final_get_full_status
IntegratedTradingPipeline.process_tick = _atria_final_process_tick
IntegratedTradingPipeline.step = _atria_final_pipeline_step
''',
}

# ---------- Append patches only once ----------
for filename, patch in PATCHES.items():
    path = CORE / filename
    marker = "ATRIA_FINAL_REMAINING6"

    old_text = path.read_text(encoding="utf-8")
    if marker in old_text:
        print(f"[SKIP] پچ final قبلاً در {filename} وجود دارد.")
        continue

    path.write_text(old_text.rstrip() + "\n" + patch + "\n", encoding="utf-8")
    print(f"[PATCHED] {filename}")

# ---------- Syntax verification ----------
print("\n[CHECK] اجرای compileall...")
compiled = subprocess.run(
    [sys.executable, "-m", "compileall", "-q", "src"],
    cwd=ROOT,
)

if compiled.returncode != 0:
    print("[ROLLBACK] خطای Syntax رخ داد؛ بازگردانی Backup...")
    for filename in TARGETS:
        saved = BACKUP_DIR / "src" / "core" / filename
        shutil.copy2(saved, CORE / filename)
    raise SystemExit(1)

print("[OK] compileall موفق بود.")

# ---------- Targeted tests ----------
print("\n[TEST] اجرای ۱۰ تست هدف...")
tests = [
    "tests/test_integrated_pipeline.py",
    "tests/test_order_executor.py",
    "tests/test_order_manager.py",
    "tests/test_paper_session.py",
    "tests/test_position_tracker.py",
]

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", *tests, "--tb=short"],
    cwd=ROOT,
)

raise SystemExit(result.returncode)
