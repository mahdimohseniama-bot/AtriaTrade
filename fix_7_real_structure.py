from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.home() / "AtriaTrade"
CORE = ROOT / "src" / "core"

# بکاپِ درست قبل از Patch خراب 15:56
BROKEN_PATCH_BACKUP = (
    ROOT / "backups" / "before_7_safe_patch_20260826_155648"
)

FILES = [
    "order_manager.py",
    "position_tracker.py",
    "risk_manager.py",
    "order_executor.py",
    "paper_session.py",
    "integrated_pipeline.py",
]

MARKER = "# === AtriaTrade REAL compatibility patch: baseline-7 ==="


def die(message):
    print(f"\n[ERROR] {message}")
    raise SystemExit(1)


def restore_clean_baseline():
    if not BROKEN_PATCH_BACKUP.is_dir():
        die(f"Backup پیدا نشد: {BROKEN_PATCH_BACKUP}")

    for filename in FILES:
        source = BROKEN_PATCH_BACKUP / filename
        target = CORE / filename

        if not source.is_file():
            die(f"فایل در Backup وجود ندارد: {source}")

        shutil.copy2(source, target)

    print("[OK] وضعیت سالمِ 7-failed بازیابی شد.")


def make_new_backup():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "backups" / f"before_real_7_fix_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for filename in FILES:
        shutil.copy2(CORE / filename, backup_dir / filename)

    print(f"[OK] Backup جدید ساخته شد: {backup_dir}")
    return backup_dir


def append_patch(filename, code):
    path = CORE / filename
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        die(f"Marker قبلی در {filename} پیدا شد؛ برای جلوگیری از Patch تکراری متوقف شد.")

    path.write_text(
        text.rstrip() + "\n\n" + MARKER + "\n" + code.strip() + "\n",
        encoding="utf-8",
    )
    print(f"[PATCHED] {filename}")


def check_compile():
    command = [
        sys.executable,
        "-m",
        "py_compile",
        *[str(CORE / item) for item in FILES],
    ]
    result = subprocess.run(command)
    if result.returncode != 0:
        die("Syntax/compile check شکست خورد.")


restore_clean_baseline()
NEW_BACKUP = make_new_backup()

# ------------------------------------------------------------------
# 1) PositionTracker واقعی:
# - update_position را به open_position وصل می‌کند.
# - get_position با symbol هم جست‌وجو می‌کند.
# - quantity را aliasِ size می‌کند.
# ------------------------------------------------------------------
append_patch("position_tracker.py", r'''
_original_position_to_dict = Position.to_dict

def _compat_position_to_dict(self):
    data = _original_position_to_dict(self)
    data["quantity"] = data["size"]
    return data

Position.to_dict = _compat_position_to_dict

@property
def _compat_quantity(self):
    return self.size

@_compat_quantity.setter
def _compat_quantity(self, value):
    self.size = float(value)

Position.quantity = _compat_quantity

_original_open_position = PositionTracker.open_position
_original_get_position = PositionTracker.get_position

def _compat_open_position(self, *args, **kwargs):
    pos = _original_open_position(self, *args, **kwargs)

    # کلید symbol برای تست‌های جدید؛ کلید position_id برای API قدیمی حفظ می‌شود.
    self.positions[pos.symbol] = pos
    return pos

def _compat_update_position(
    self,
    symbol,
    side,
    quantity=None,
    entry_price=0.0,
    size=None,
    **kwargs
):
    actual_size = quantity
    if actual_size is None:
        actual_size = size
    if actual_size is None:
        actual_size = kwargs.pop("amount", 0.0)

    return self.open_position(
        symbol=symbol,
        side=side,
        size=float(actual_size),
        entry_price=float(entry_price),
        **kwargs
    )

def _compat_get_position(self, key):
    key = str(key).upper()

    # اول کلیدهای قدیمی (position_id) را امتحان کن.
    direct = _original_get_position(self, key)
    if direct is not None:
        return direct

    # سپس symbol را جست‌وجو کن.
    seen = set()
    for position in self.positions.values():
        if id(position) in seen:
            continue
        seen.add(id(position))

        if getattr(position, "symbol", "").upper() == key:
            return position

    return None

PositionTracker.open_position = _compat_open_position
PositionTracker.update_position = _compat_update_position
PositionTracker.get_position = _compat_get_position
''')

# ------------------------------------------------------------------
# 2) RiskConfig: پذیرش aliasهای جدید، بدون حذف سازگاری قدیمی.
# ------------------------------------------------------------------
append_patch("risk_manager.py", r'''
import inspect as _compat_inspect

_original_riskconfig_init = RiskConfig.__init__

def _compat_riskconfig_init(self, *args, **kwargs):
    kwargs = dict(kwargs)

    risk_pct = kwargs.pop(
        "risk_per_trade_pct",
        kwargs.pop("max_risk_per_trade_pct", None),
    )
    daily_pct = kwargs.pop("max_daily_loss_pct", None)

    # گزینه‌های config که بعضی مصرف‌کننده‌ها می‌دهند اما نسخه قدیمی نمی‌شناسد.
    kwargs.pop("stop_loss_pct", None)
    kwargs.pop("take_profit_pct", None)
    kwargs.pop("min_trade_value", None)
    kwargs.pop("initial_capital", None)

    signature = _compat_inspect.signature(_original_riskconfig_init)
    valid_names = set(signature.parameters.keys())

    if risk_pct is not None and "max_risk_per_trade_percent" in valid_names:
        value = float(risk_pct)
        kwargs.setdefault(
            "max_risk_per_trade_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    if daily_pct is not None and "max_daily_loss_percent" in valid_names:
        value = float(daily_pct)
        kwargs.setdefault(
            "max_daily_loss_percent",
            value * 100.0 if 0 < value <= 1.0 else value,
        )

    kwargs = {key: value for key, value in kwargs.items() if key in valid_names}
    _original_riskconfig_init(self, *args, **kwargs)

    percent = float(getattr(self, "max_risk_per_trade_percent", 0.0))
    daily_percent = float(getattr(self, "max_daily_loss_percent", 0.0))

    self.risk_per_trade_pct = (
        float(risk_pct) if risk_pct is not None else percent / 100.0
    )
    self.max_risk_per_trade_pct = self.risk_per_trade_pct
    self.max_daily_loss_pct = (
        float(daily_pct) if daily_pct is not None else daily_percent / 100.0
    )

RiskConfig.__init__ = _compat_riskconfig_init
''')

# ------------------------------------------------------------------
# 3) OrderManager: validation + LIMIT => OPEN.
# ------------------------------------------------------------------
append_patch("order_manager.py", r'''
_original_create_order = OrderManager.create_order

def _compat_enum_value(value):
    return getattr(value, "value", value)

def _compat_create_order(
    self,
    symbol,
    side,
    order_type="MARKET",
    quantity=0.0,
    price=0.0,
    **kwargs
):
    clean_side = str(_compat_enum_value(side)).upper()
    clean_type = str(_compat_enum_value(order_type)).upper()

    if clean_side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side: {side}")

    if clean_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError(f"Invalid order type: {order_type}")

    actual_quantity = kwargs.get("amount", kwargs.get("size", quantity))
    if float(actual_quantity) <= 0:
        raise ValueError("Quantity must be greater than zero")

    actual_price = kwargs.get("entry_price", price)
    if clean_type in ("LIMIT", "STOP") and float(actual_price or 0.0) <= 0:
        raise ValueError(f"{clean_type} order requires a positive price")

    order = _original_create_order(
        self,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        **kwargs
    )

    if clean_type == "LIMIT":
        order.status = "OPEN"

    return order

OrderManager.create_order = _compat_create_order
''')

# ------------------------------------------------------------------
# 4) OrderExecutor: API جدید current_price/sl/tp + اجرای Limit.
# ------------------------------------------------------------------
append_patch("order_executor.py", r'''
def _compat_as_dict(item):
    return item.to_dict() if hasattr(item, "to_dict") else item

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
    **kwargs
):
    execution_price = current_price if current_price is not None else price

    if execution_price is None:
        raise ValueError("current_price or price is required")

    order = self.execute_market_order(
        symbol=symbol,
        side=side,
        quantity=float(quantity),
        price=float(execution_price),
        stop_loss=sl if sl is not None else stop_loss,
        take_profit=tp if tp is not None else take_profit,
    )

    position = self.position_tracker.get_position(symbol)

    return {
        "order": _compat_as_dict(order),
        "position": _compat_as_dict(position),
        "status": "FILLED",
    }

def _compat_process_limit_orders(self, current_market_prices):
    triggered = []

    for order in list(self.order_manager.orders.values()):
        status = str(getattr(getattr(order, "status", ""), "value",
                             getattr(order, "status", ""))).upper()

        order_type = str(getattr(getattr(order, "order_type", ""), "value",
                                 getattr(order, "order_type", ""))).upper()

        if status not in ("OPEN", "PENDING") or order_type != "LIMIT":
            continue

        symbol = str(order.symbol).upper()
        if symbol not in current_market_prices:
            continue

        market_price = float(current_market_prices[symbol])
        limit_price = float(order.price)

        side = str(getattr(getattr(order, "side", ""), "value",
                           getattr(order, "side", ""))).upper()

        should_fill = (
            (side == "BUY" and market_price <= limit_price)
            or (side == "SELL" and market_price >= limit_price)
        )

        if not should_fill:
            continue

        order.status = "FILLED"
        order.filled_price = market_price
        order.executed_price = market_price

        self.position_tracker.update_position(
            symbol=symbol,
            side=side,
            quantity=float(order.quantity),
            entry_price=market_price,
        )
        triggered.append(order)

    return triggered

OrderExecutor.place_and_execute_market_order = _compat_place_and_execute_market_order
OrderExecutor.process_limit_orders = _compat_process_limit_orders
''')

# ------------------------------------------------------------------
# 5) PaperTradingSession واقعی:
# زیرکلاس PaperSession است تا API قدیمی PaperSession دست‌نخورده بماند.
# ------------------------------------------------------------------
append_patch("paper_session.py", r'''
class PaperTradingSession(PaperSession):
    """Adapter جدید برای چرخه معاملات کاغذی، با حفظ PaperSession قدیمی."""

    def __init__(self, initial_balance=10000.0, risk_config=None, **kwargs):
        super().__init__(
            session_name=kwargs.pop("session_name", "paper_trading"),
            initial_capital=float(initial_balance),
            currency=kwargs.pop("currency", "USDT"),
            session_id=kwargs.pop("session_id", "paper_trading"),
        )

        from src.core.position_tracker import PositionTracker
        from src.core.order_executor import OrderExecutor

        self.risk_config = risk_config
        self.position_tracker = PositionTracker()
        self.order_executor = OrderExecutor(
            position_tracker=self.position_tracker
        )
        self.market_prices = {}

    def get_balance(self):
        return self.current_capital

    def update_market_prices(self, prices):
        normalized = {
            str(symbol).upper(): float(price)
            for symbol, price in prices.items()
        }
        self.market_prices.update(normalized)
        self.position_tracker.update_prices(normalized)

    def get_equity(self):
        equity = float(self.current_capital)
        seen = set()

        for position in self.position_tracker.positions.values():
            if id(position) in seen:
                continue
            seen.add(id(position))

            if not position.is_open:
                continue

            market_price = self.market_prices.get(
                position.symbol, position.current_price
            )

            # در BUY هنگام ورود، cost از current_capital کسر شده؛
            # برای Equity باید ارزش فعلی دارایی اضافه شود.
            if position.side == "BUY":
                equity += position.size * float(market_price)
            else:
                # مدل ساده short: collateral ورود + سود/زیان.
                equity += (
                    position.size * position.entry_price
                    + position.size * (position.entry_price - float(market_price))
                )

        return equity

    def execute_order(
        self,
        symbol,
        side,
        quantity,
        price,
        sl=None,
        tp=None,
        stop_loss=None,
        take_profit=None,
        **kwargs
    ):
        side_text = str(getattr(side, "value", side)).upper()
        quantity = float(quantity)
        price = float(price)

        if side_text == "BUY":
            self.current_capital -= quantity * price
        elif side_text == "SELL":
            self.current_capital += quantity * price
        else:
            raise ValueError(f"Invalid order side: {side}")

        self.updated_at = self._now()

        return self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=side_text,
            quantity=quantity,
            current_price=price,
            sl=sl if sl is not None else stop_loss,
            tp=tp if tp is not None else take_profit,
        )
''')

# ------------------------------------------------------------------
# 6) Pipeline: ارسال Strategy Decision به Executor.
# ------------------------------------------------------------------
append_patch("integrated_pipeline.py", r'''
def _compat_pipeline_step(self, market_data):
    breaker = getattr(self.risk_manager, "circuit_breaker_tripped", False)
    if callable(breaker):
        breaker = breaker()

    if breaker:
        return {"action": "HOLD", "blocked": True}

    if not callable(getattr(self, "strategy", None)):
        return {"action": "HOLD", "status": "NO_STRATEGY"}

    decision = self.strategy(market_data) or {}
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

    if price is None or float(price) <= 0 or quantity <= 0:
        return {"action": "HOLD", "blocked": True, "reason": "INVALID_SIGNAL"}

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
    check_compile()
except SystemExit:
    print("[ROLLBACK] Compile ناموفق بود؛ بازگشت به Backup جدید...")
    for filename in FILES:
        shutil.copy2(NEW_BACKUP / filename, CORE / filename)
    raise

print("\n[OK] Patch واقعی با ساختار فعلی پروژه اعمال شد.")
