from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.home() / "AtriaTrade"
CORE = ROOT / "src" / "core"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = ROOT / "backups" / f"before_7_safe_patch_{STAMP}"

FILES = [
    "order_manager.py",
    "order_executor.py",
    "position_tracker.py",
    "risk_manager.py",
    "paper_session.py",
    "integrated_pipeline.py",
]

MARKER = "# === AtriaTrade compatibility patch: baseline-7 ==="


def backup() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = CORE / name
        if not src.exists():
            raise FileNotFoundError(f"Required file not found: {src}")
        shutil.copy2(src, BACKUP / name)
    print(f"[OK] Backup created: {BACKUP}")


def append_once(filename: str, code: str) -> None:
    target = CORE / filename
    content = target.read_text(encoding="utf-8")

    if MARKER in content:
        print(f"[SKIP] Compatibility patch already exists: {filename}")
        return

    target.write_text(
        content.rstrip() + "\n\n" + MARKER + "\n" + code.strip() + "\n",
        encoding="utf-8",
    )
    print(f"[PATCHED] {filename}")


def restore() -> None:
    if not BACKUP.exists():
        return
    for name in FILES:
        saved = BACKUP / name
        if saved.exists():
            shutil.copy2(saved, CORE / name)
    print("[ROLLBACK] Files restored because compile check failed.")


def compile_check() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", *[str(CORE / f) for f in FILES]],
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Python compilation failed.")


backup()

append_once("order_manager.py", r'''
# Compatibility: accept Enum/string inputs, validate public orders,
# and expose LIMIT orders as OPEN without changing the existing Order class.
_compat_original_create_order = OrderManager.create_order

def _compat_order_value(value):
    return getattr(value, "value", value)

def _compat_create_order(
    self, symbol, side, order_type="MARKET", quantity=0.0, price=0.0, **kwargs
):
    raw_side = str(_compat_order_value(side)).upper()
    raw_type = str(_compat_order_value(order_type)).upper()

    if raw_side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side: {side}")

    if raw_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError(f"Invalid order type: {order_type}")

    effective_quantity = kwargs.get("amount", kwargs.get("size", quantity))
    try:
        effective_quantity = float(effective_quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be numeric") from exc

    if effective_quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    effective_price = kwargs.get("entry_price", price)
    try:
        effective_price = float(effective_price or 0.0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Price must be numeric") from exc

    if raw_type in ("LIMIT", "STOP") and effective_price <= 0:
        raise ValueError(f"{raw_type} order requires a positive price")

    order = _compat_original_create_order(
        self,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        **kwargs,
    )

    if raw_type == "LIMIT":
        order.status = "OPEN"

    return order

OrderManager.create_order = _compat_create_order

# Add OPEN only when the historic enum did not expose it.
if not hasattr(OrderStatus, "OPEN"):
    # String status is intentionally used by the compatibility wrapper above.
    setattr(OrderStatus, "OPEN", "OPEN")
''')

append_once("position_tracker.py", r'''
# Compatibility: index positions by symbol too and keep size/quantity aliases synced.
_compat_original_update_position = PositionTracker.update_position
_compat_original_get_position = PositionTracker.get_position

def _compat_set_position_aliases(position, quantity=None):
    if position is None:
        return position

    if isinstance(position, dict):
        value = position.get("quantity", position.get("size", quantity))
        if value is not None:
            position["quantity"] = float(value)
            position["size"] = float(value)
        return position

    value = getattr(position, "quantity", getattr(position, "size", quantity))
    if value is not None:
        try:
            position.quantity = float(value)
        except Exception:
            pass
        try:
            position.size = float(value)
        except Exception:
            pass
    return position

def _compat_update_position(self, symbol, side, quantity=None, entry_price=0.0, **kwargs):
    if quantity is None:
        quantity = kwargs.get("size", kwargs.get("amount", 0.0))

    position = _compat_original_update_position(
        self,
        symbol=symbol,
        side=side,
        quantity=quantity,
        entry_price=entry_price,
        **kwargs,
    )

    position = _compat_set_position_aliases(position, quantity)
    key = str(symbol).upper()

    # Historic implementations may index by position_id only.
    try:
        self.positions[key] = position
    except Exception:
        pass

    return position

def _compat_get_position(self, symbol):
    key = str(symbol).upper()

    try:
        found = _compat_original_get_position(self, key)
    except Exception:
        found = None

    if found is not None:
        return _compat_set_position_aliases(found)

    positions = getattr(self, "positions", {})
    if isinstance(positions, dict):
        direct = positions.get(key)
        if direct is not None:
            return _compat_set_position_aliases(direct)

        seen = set()
        for position in positions.values():
            if id(position) in seen:
                continue
            seen.add(id(position))
            pos_symbol = (
                position.get("symbol")
                if isinstance(position, dict)
                else getattr(position, "symbol", None)
            )
            if str(pos_symbol).upper() == key:
                return _compat_set_position_aliases(position)

    return None

PositionTracker.update_position = _compat_update_position
PositionTracker.get_position = _compat_get_position
''')

append_once("risk_manager.py", r'''
# Compatibility: accept old/new RiskConfig keyword aliases.
import inspect as _compat_inspect

_compat_original_riskconfig_init = RiskConfig.__init__

def _compat_riskconfig_init(self, *args, **kwargs):
    supplied = dict(kwargs)

    # Aliases used by PaperTradingSession and legacy tests.
    risk_pct = supplied.pop(
        "risk_per_trade_pct",
        supplied.pop("max_risk_per_trade_pct", None),
    )
    daily_pct = supplied.pop("max_daily_loss_pct", None)

    # Parameters accepted for strategy/session configuration but not required
    # by this historic RiskConfig implementation.
    supplied.pop("stop_loss_pct", None)
    supplied.pop("take_profit_pct", None)
    supplied.pop("min_trade_value", None)

    signature = _compat_inspect.signature(_compat_original_riskconfig_init)
    accepted = set(signature.parameters)

    if risk_pct is not None and "max_risk_per_trade_percent" in accepted:
        value = float(risk_pct)
        supplied.setdefault(
            "max_risk_per_trade_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    if daily_pct is not None and "max_daily_loss_percent" in accepted:
        value = float(daily_pct)
        supplied.setdefault(
            "max_daily_loss_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    filtered = {k: v for k, v in supplied.items() if k in accepted}
    _compat_original_riskconfig_init(self, *args, **filtered)

    risk_percent = float(
        getattr(self, "max_risk_per_trade_percent", 0.0)
    )
    daily_percent = float(
        getattr(self, "max_daily_loss_percent", 0.0)
    )

    self.risk_per_trade_pct = (
        float(risk_pct)
        if risk_pct is not None
        else risk_percent / 100.0
    )
    self.max_risk_per_trade_pct = self.risk_per_trade_pct
    self.max_daily_loss_pct = (
        float(daily_pct)
        if daily_pct is not None
        else daily_percent / 100.0
    )

RiskConfig.__init__ = _compat_riskconfig_init
''')

append_once("order_executor.py", r'''
# Compatibility: preserve execute_market_order's historic Order return type,
# while the explicit current_price/sl/tp public form returns order + position.
_compat_original_place_market = OrderExecutor.place_and_execute_market_order

def _compat_position_to_dict(position):
    if position is None:
        return None
    if hasattr(position, "to_dict"):
        return position.to_dict()
    return position

def _compat_order_to_dict(order):
    if hasattr(order, "to_dict"):
        return order.to_dict()
    return order

def _compat_place_and_execute_market_order(
    self,
    symbol,
    side,
    quantity,
    current_price=None,
    price=None,
    sl=None,
    tp=None,
    stop_loss=None,
    take_profit=None,
    **kwargs,
):
    modern_api = (
        current_price is not None
        or sl is not None
        or tp is not None
    )

    execution_price = (
        current_price
        if current_price is not None
        else price
    )

    if execution_price is None:
        # Keep historic behaviour for calls that use the old positional shape.
        return _compat_original_place_market(
            self, symbol, side, quantity, **kwargs
        )

    order = self.execute_market_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=float(execution_price),
        stop_loss=sl if sl is not None else stop_loss,
        take_profit=tp if tp is not None else take_profit,
    )

    if not modern_api:
        return order

    position = self.position_tracker.get_position(symbol)
    return {
        "order": _compat_order_to_dict(order),
        "position": _compat_position_to_dict(position),
        "status": "FILLED",
    }

def _compat_process_limit_orders(self, current_market_prices):
    triggered = []

    for order in list(getattr(self.order_manager, "orders", {}).values()):
        status = getattr(order, "status", None)
        status = getattr(status, "value", status)
        if str(status).upper() not in ("OPEN", "PENDING"):
            continue

        order_type = getattr(order, "order_type", "LIMIT")
        order_type = getattr(order_type, "value", order_type)
        if str(order_type).upper() != "LIMIT":
            continue

        symbol = str(getattr(order, "symbol", "")).upper()
        market_price = current_market_prices.get(symbol)
        if market_price is None:
            continue

        side = getattr(order, "side", "")
        side = str(getattr(side, "value", side)).upper()
        limit_price = float(getattr(order, "price", 0.0))
        market_price = float(market_price)

        fills = (
            (side == "BUY" and market_price <= limit_price)
            or (side == "SELL" and market_price >= limit_price)
        )
        if not fills:
            continue

        order.status = "FILLED"
        try:
            order.filled_price = market_price
            order.executed_price = market_price
        except Exception:
            pass

        self.position_tracker.update_position(
            symbol=symbol,
            side=side,
            quantity=float(getattr(order, "quantity", 0.0)),
            entry_price=market_price,
        )
        triggered.append(order)

    return triggered

OrderExecutor.place_and_execute_market_order = _compat_place_and_execute_market_order
OrderExecutor.process_limit_orders = _compat_process_limit_orders
''')

append_once("paper_session.py", r'''
# Compatibility: retain the original accounting implementation, but provide
# deterministic mark-to-market equity for the public paper-session API.
_compat_original_update_market_prices = PaperTradingSession.update_market_prices
_compat_original_get_equity = PaperTradingSession.get_equity

def _compat_session_update_market_prices(self, prices):
    cache = getattr(self, "_compat_market_prices", {})
    cache.update({str(k).upper(): float(v) for k, v in prices.items()})
    self._compat_market_prices = cache
    return _compat_original_update_market_prices(self, prices)

def _compat_session_value(position, key, default=0.0):
    if isinstance(position, dict):
        return position.get(key, default)
    return getattr(position, key, default)

def _compat_session_get_equity(self):
    # If no fresh market prices were supplied, preserve original behaviour.
    prices = getattr(self, "_compat_market_prices", {})
    if not prices:
        return _compat_original_get_equity(self)

    balance = getattr(self, "balance", getattr(self, "cash_balance", None))
    tracker = getattr(self, "position_tracker", None)

    if balance is None or tracker is None:
        return _compat_original_get_equity(self)

    equity = float(balance)
    processed = set()

    for symbol, market_price in prices.items():
        position = tracker.get_position(symbol)
        if position is None or id(position) in processed:
            continue
        processed.add(id(position))

        quantity = float(
            _compat_session_value(
                position,
                "quantity",
                _compat_session_value(position, "size", 0.0),
            )
        )
        entry = float(_compat_session_value(position, "entry_price", 0.0))
        side = str(_compat_session_value(position, "side", "BUY")).upper()

        # Cash was reduced at BUY entry; add current marked position value.
        # For a short, represent value as entry collateral plus its PnL.
        if side == "SELL":
            equity += quantity * entry + quantity * (entry - float(market_price))
        else:
            equity += quantity * float(market_price)

    return equity

PaperTradingSession.update_market_prices = _compat_session_update_market_prices
PaperTradingSession.get_equity = _compat_session_get_equity

# Preserve the legacy import name.
if "PaperSession" not in globals():
    PaperSession = PaperTradingSession
''')

append_once("integrated_pipeline.py", r'''
# Compatibility: execute BUY/SELL decisions from an injected strategy.
def _compat_pipeline_step(self, market_data):
    breaker = getattr(self.risk_manager, "circuit_breaker_tripped", False)
    if callable(breaker):
        breaker = breaker()

    if breaker:
        return {"action": "HOLD", "blocked": True}

    strategy = getattr(self, "strategy", None)
    if not callable(strategy):
        return {"action": "HOLD", "status": "NO_STRATEGY"}

    decision = strategy(market_data) or {}
    action = str(decision.get("action", "HOLD")).upper()

    if action not in ("BUY", "SELL"):
        return {"action": "HOLD"}

    symbol = str(decision.get("symbol", "BTCUSDT")).upper()
    quantity = float(decision.get("quantity", decision.get("size", 0.0)))

    price = decision.get("price", decision.get("current_price"))
    if price is None:
        tick = market_data.get(symbol, {})
        if isinstance(tick, dict):
            price = tick.get("price", tick.get("close"))
    if price is None or float(price) <= 0:
        return {"action": "HOLD", "blocked": True, "reason": "MISSING_PRICE"}

    result = self.order_executor.place_and_execute_market_order(
        symbol=symbol,
        side=action,
        quantity=quantity,
        current_price=float(price),
        sl=decision.get("sl", decision.get("stop_loss")),
        tp=decision.get("tp", decision.get("take_profit")),
    )

    return {
        "action": action,
        "order": result["order"],
        "position": result.get("position"),
        "status": result.get("status", "FILLED"),
    }

IntegratedTradingPipeline.step = _compat_pipeline_step
IntegratedTradingPipeline.process_tick = _compat_pipeline_step
''')

try:
    compile_check()
except Exception as exc:
    print(f"[ERROR] {exc}")
    restore()
    raise SystemExit(1)

print("\n[OK] Patch applied successfully.")
print("\nRun targeted tests:")
print(
    "python -m pytest -q "
    "tests/test_order_manager.py "
    "tests/test_order_executor.py "
    "tests/test_position_tracker.py "
    "tests/test_paper_session.py "
    "tests/test_integrated_pipeline.py"
)
