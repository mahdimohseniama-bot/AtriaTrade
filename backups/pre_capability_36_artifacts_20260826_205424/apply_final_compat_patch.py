from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / f".compat_patch_backup_{STAMP}"

TARGETS = [
    Path("src/core/order_manager.py"),
    Path("src/core/order_executor.py"),
    Path("src/core/risk_manager.py"),
    Path("src/core/position_tracker.py"),
    Path("src/core/paper_session.py"),
    Path("src/core/integrated_pipeline.py"),
]

MARKER = "# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ==="

PATCHES = {
    Path("src/core/order_manager.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Compatibility layer: validation + OPEN state for LIMIT orders.

_original_create_order = OrderManager.create_order

def _atriatrade_create_order_compat(
    self,
    symbol,
    side,
    order_type="MARKET",
    quantity=0.0,
    price=0.0,
    **kwargs,
):
    side_value = str(getattr(side, "value", side)).strip().upper()
    type_value = str(getattr(order_type, "value", order_type)).strip().upper()

    amount = kwargs.get("amount", kwargs.get("size", quantity))
    unit_price = kwargs.get("entry_price", price)

    if side_value not in {"BUY", "SELL"}:
        raise ValueError(f"Invalid order side: {side}")

    if type_value not in {"MARKET", "LIMIT", "STOP"}:
        raise ValueError(f"Invalid order type: {order_type}")

    try:
        amount_value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError("Order quantity must be numeric") from exc

    if amount_value <= 0:
        raise ValueError("Order quantity must be positive")

    try:
        price_value = float(unit_price) if unit_price is not None else 0.0
    except (TypeError, ValueError) as exc:
        raise ValueError("Order price must be numeric") from exc

    if type_value in {"LIMIT", "STOP"} and price_value <= 0:
        raise ValueError(f"{type_value} order requires a positive price")

    order = _original_create_order(
        self,
        symbol=symbol,
        side=side_value,
        order_type=type_value,
        quantity=amount_value,
        price=price_value,
        **kwargs,
    )

    if type_value == "LIMIT":
        order.status = "OPEN"

    return order

OrderManager.create_order = _atriatrade_create_order_compat
''',

    Path("src/core/order_executor.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Public wrapper with the result format required by paper/integrated flows.

def _atriatrade_place_and_execute_market_order(
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
    execution_price = current_price
    if execution_price is None:
        execution_price = price
    if execution_price is None:
        execution_price = kwargs.get("price", 0.0)

    execution_price = float(execution_price)
    resolved_sl = sl if sl is not None else stop_loss
    resolved_tp = tp if tp is not None else take_profit

    order = self.execute_market_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=execution_price,
        stop_loss=resolved_sl,
        take_profit=resolved_tp,
    )

    position = self.position_tracker.get_position(symbol)
    if position is None:
        position_data = {
            "symbol": str(symbol).upper(),
            "side": str(getattr(side, "value", side)).upper(),
            "quantity": float(quantity),
            "size": float(quantity),
            "entry_price": execution_price,
        }
    elif isinstance(position, dict):
        position_data = dict(position)
    else:
        position_data = dict(getattr(position, "__dict__", {}))

    position_data.setdefault("symbol", str(symbol).upper())
    position_data.setdefault("quantity", float(quantity))
    position_data.setdefault("size", position_data["quantity"])
    position_data.setdefault("entry_price", execution_price)

    order_data = order.to_dict() if hasattr(order, "to_dict") else order
    return {
        "order": order_data,
        "position": position_data,
        "status": "FILLED",
    }

OrderExecutor.place_and_execute_market_order = _atriatrade_place_and_execute_market_order


_original_process_limit_orders = OrderExecutor.process_limit_orders

def _atriatrade_process_limit_orders_compat(self, *args, **kwargs):
    open_orders = [
        order for order in self.order_manager.orders.values()
        if getattr(order, "order_type", "").upper() == "LIMIT"
        and getattr(order, "status", "").upper() == "OPEN"
    ]

    for order in open_orders:
        order.status = "PENDING"

    try:
        result = _original_process_limit_orders(self, *args, **kwargs)
    finally:
        for order in open_orders:
            if getattr(order, "status", "").upper() == "PENDING":
                order.status = "OPEN"

    return result

OrderExecutor.process_limit_orders = _atriatrade_process_limit_orders_compat
''',

    Path("src/core/risk_manager.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Accept both historical '*_percent' names and test/paper '*_pct' aliases.

_original_risk_config_init = RiskConfig.__init__

def _atriatrade_risk_config_init_compat(
    self,
    max_risk_per_trade_percent=2.0,
    max_daily_loss_percent=5.0,
    max_position_percent=10.0,
    *args,
    **kwargs,
):
    trade_risk = kwargs.pop(
        "risk_per_trade_pct",
        kwargs.pop(
            "max_risk_per_trade_pct",
            kwargs.pop("max_risk_per_trade_percent", max_risk_per_trade_percent),
        ),
    )
    daily_loss = kwargs.pop(
        "max_daily_loss_pct",
        kwargs.pop("max_daily_loss_percent", max_daily_loss_percent),
    )

    _original_risk_config_init(
        self,
        max_risk_per_trade_percent=trade_risk,
        max_daily_loss_percent=daily_loss,
        max_position_percent=max_position_percent,
        *args,
        **kwargs,
    )

    self.risk_per_trade_pct = float(trade_risk)
    self.max_risk_per_trade_pct = float(trade_risk)
    self.max_risk_per_trade_percent = float(trade_risk)
    self.max_daily_loss_pct = float(daily_loss)
    self.max_daily_loss_percent = float(daily_loss)

RiskConfig.__init__ = _atriatrade_risk_config_init_compat
''',

    Path("src/core/position_tracker.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Normalize position output without replacing the original tracker logic.

_original_update_position = PositionTracker.update_position
_original_get_position = PositionTracker.get_position

def _atriatrade_normalize_position(position):
    if position is None:
        return None

    if isinstance(position, dict):
        if "quantity" not in position and "size" in position:
            position["quantity"] = position["size"]
        if "size" not in position and "quantity" in position:
            position["size"] = position["quantity"]
        return position

    if not hasattr(position, "size") and hasattr(position, "quantity"):
        setattr(position, "size", getattr(position, "quantity"))
    return position

def _atriatrade_update_position_compat(self, *args, **kwargs):
    return _atriatrade_normalize_position(_original_update_position(self, *args, **kwargs))

def _atriatrade_get_position_compat(self, symbol, *args, **kwargs):
    return _atriatrade_normalize_position(_original_get_position(self, symbol, *args, **kwargs))

PositionTracker.update_position = _atriatrade_update_position_compat
PositionTracker.get_position = _atriatrade_get_position_compat
''',

    Path("src/core/paper_session.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Equity = cash balance + current marked-to-market value of all open positions.

def _atriatrade_get_equity_compat(self):
    equity = float(self.balance)

    tracker = getattr(self, "position_tracker", None)
    positions = getattr(tracker, "positions", {}) if tracker is not None else {}

    for symbol, position in positions.items():
        if isinstance(position, dict):
            quantity = float(position.get("quantity", position.get("size", 0.0)))
            entry_price = float(position.get("entry_price", 0.0))
            side = str(position.get("side", "BUY")).upper()
        else:
            quantity = float(getattr(position, "quantity", getattr(position, "size", 0.0)))
            entry_price = float(getattr(position, "entry_price", 0.0))
            side = str(getattr(position, "side", "BUY")).upper()

        market_price = float(
            getattr(self, "market_prices", {}).get(str(symbol).upper(), entry_price)
        )

        if side == "SELL":
            equity += quantity * ((2.0 * entry_price) - market_price)
        else:
            equity += quantity * market_price

    return float(equity)

PaperTradingSession.get_equity = _atriatrade_get_equity_compat
''',

    Path("src/core/integrated_pipeline.py"): r'''

# === ATRIATRADE FINAL COMPATIBILITY PATCH v1 ===
# Execute strategy BUY/SELL signals and stop immediately on circuit breaker.

def _atriatrade_pipeline_step_compat(self, market_data):
    if getattr(self.risk_manager, "circuit_breaker_tripped", False):
        return {
            "action": "HOLD",
            "blocked": True,
            "reason": "Circuit breaker active",
        }

    if callable(getattr(self, "strategy", None)):
        signal = self.strategy(market_data)
    else:
        signal = next(
            (
                value for value in market_data.values()
                if isinstance(value, dict) and "action" in value
            ),
            {"action": "HOLD"},
        )

    if not isinstance(signal, dict):
        return {"action": "HOLD", "status": "SKIPPED"}

    action = str(signal.get("action", "HOLD")).upper()
    if action not in {"BUY", "SELL"}:
        return {"action": "HOLD", "status": "SKIPPED"}

    symbol = str(signal.get("symbol", "BTCUSDT")).upper()
    quantity = float(signal.get("quantity", signal.get("size", 0.0)))
    if quantity <= 0:
        return {
            "action": "HOLD",
            "blocked": True,
            "reason": "Invalid signal quantity",
        }

    tick = market_data.get(symbol, {})
    if not isinstance(tick, dict):
        tick = {}

    price = tick.get("price", tick.get("close", signal.get("price", 0.0)))
    price = float(price)

    result = self.order_executor.place_and_execute_market_order(
        symbol=symbol,
        side=action,
        quantity=quantity,
        current_price=price,
        sl=signal.get("sl", signal.get("stop_loss")),
        tp=signal.get("tp", signal.get("take_profit")),
    )

    return {
        "action": action,
        "order": result.get("order"),
        "position": result.get("position"),
        "status": "EXECUTED",
    }

IntegratedTradingPipeline.step = _atriatrade_pipeline_step_compat
''',
}


def restore() -> None:
    if not BACKUP_DIR.exists():
        return

    for relative_path in TARGETS:
        source = BACKUP_DIR / relative_path
        destination = ROOT / relative_path
        if source.exists():
            shutil.copy2(source, destination)

    print("\nRESTORED: original files restored from:")
    print(BACKUP_DIR)


def main() -> int:
    missing = [str(path) for path in TARGETS if not (ROOT / path).is_file()]
    if missing:
        print("ERROR: required files are missing:")
        print("\n".join(missing))
        return 1

    already_patched = []
    for relative_path in TARGETS:
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        if MARKER in content:
            already_patched.append(str(relative_path))

    if already_patched:
        print("STOP: Patch marker already exists in:")
        print("\n".join(already_patched))
        print("No changes were made.")
        return 2

    BACKUP_DIR.mkdir(parents=True, exist_ok=False)
    for relative_path in TARGETS:
        source = ROOT / relative_path
        destination = BACKUP_DIR / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    print(f"BACKUP_CREATED: {BACKUP_DIR}")

    try:
        for relative_path, patch in PATCHES.items():
            path = ROOT / relative_path
            original = path.read_text(encoding="utf-8")
            path.write_text(
                original.rstrip() + "\n" + patch.lstrip(),
                encoding="utf-8",
            )

        compile_command = [
            sys.executable,
            "-m",
            "py_compile",
            *[str(path) for path in TARGETS],
        ]
        compile_result = subprocess.run(compile_command, check=False)

        if compile_result.returncode != 0:
            print("ERROR: Syntax check failed; restoring original files.")
            restore()
            return compile_result.returncode

        print("PATCH_APPLIED_AND_SYNTAX_OK")
        print(f"Backup location: {BACKUP_DIR}")
        return 0

    except Exception as exc:
        print(f"ERROR: Patch application failed: {exc}")
        restore()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
