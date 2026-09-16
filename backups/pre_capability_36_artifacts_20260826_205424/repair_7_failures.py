from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path.home() / "AtriaTrade"
CORE = ROOT / "src" / "core"

if not CORE.is_dir():
    raise SystemExit(f"ERROR: مسیر پیدا نشد: {CORE}")

backup = ROOT / "backups" / f"before_repair_7_{datetime.now():%Y%m%d_%H%M%S}"
backup.mkdir(parents=True, exist_ok=True)

targets = [
    "order_manager.py",
    "position_tracker.py",
    "risk_manager.py",
    "order_executor.py",
    "paper_session.py",
    "integrated_pipeline.py",
]

for name in targets:
    src = CORE / name
    if src.exists():
        shutil.copy2(src, backup / name)

print(f"[1/5] Backup created: {backup}")

files = {
"order_manager.py": r'''import time
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order:
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: Any,
        order_type: Any,
        quantity: float,
        price: float = 0.0,
        status: Any = "PENDING",
        **kwargs: Any,
    ) -> None:
        self.order_id = str(order_id)
        self.symbol = str(symbol).upper()
        self.side = str(getattr(side, "value", side)).upper()
        self.order_type = str(getattr(order_type, "value", order_type)).upper()
        self.quantity = float(quantity)
        self.size = self.quantity
        self.price = float(price or 0.0)
        self.status = str(getattr(status, "value", status)).upper()
        self.created_at = time.time()
        self.filled_at = None
        self.executed_price = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "size": self.size,
            "price": self.price,
            "status": self.status,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "executed_price": self.executed_price,
        }

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class OrderManager:
    def __init__(self, **kwargs: Any) -> None:
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

    def create_order(
        self,
        symbol: str,
        side: Any,
        order_type: Any = "MARKET",
        quantity: float = 0.0,
        price: Optional[float] = None,
        **kwargs: Any,
    ) -> Order:
        side_value = str(getattr(side, "value", side)).strip().upper()
        type_value = str(
            getattr(order_type, "value", order_type or "MARKET")
        ).strip().upper()

        amount = kwargs.get("amount", kwargs.get("size", quantity))
        order_price = kwargs.get("entry_price", price)

        if side_value not in {"BUY", "SELL"}:
            raise ValueError(f"Invalid order side: {side}")

        if type_value not in {"MARKET", "LIMIT", "STOP"}:
            raise ValueError(f"Invalid order type: {order_type}")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError("Quantity must be numeric")

        if amount <= 0:
            raise ValueError("Quantity must be greater than zero")

        if order_price is None:
            order_price = 0.0

        try:
            order_price = float(order_price)
        except (TypeError, ValueError):
            raise ValueError("Price must be numeric")

        if type_value in {"LIMIT", "STOP"} and order_price <= 0:
            raise ValueError("Limit/stop order requires a positive price")

        order_id = str(kwargs.get(
            "order_id",
            f"ord_{len(self.orders) + len(self.order_history) + 1}_{int(time.time() * 1000)}",
        ))

        # LIMIT در این پروژه باید OPEN باشد تا process_limit_orders آن را ببیند.
        initial_status = OrderStatus.OPEN.value if type_value == "LIMIT" else OrderStatus.PENDING.value

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side_value,
            order_type=type_value,
            quantity=amount,
            price=order_price,
            status=initial_status,
        )
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(str(order_id))

    def cancel_order(self, order_id: str) -> Optional[Order]:
        order = self.orders.get(str(order_id))
        if order is None:
            return None
        order.status = OrderStatus.CANCELLED.value
        return order

    def get_open_orders(self) -> List[Order]:
        return [
            order for order in self.orders.values()
            if order.status in {OrderStatus.OPEN.value, OrderStatus.PENDING.value}
        ]
''',

"position_tracker.py": r'''import time
from typing import Any, Dict, Optional


class PositionDict(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(
                f"'PositionDict' object has no attribute '{name}'"
            ) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class PositionTracker:
    def __init__(self, **kwargs: Any) -> None:
        self.positions: Dict[str, PositionDict] = {}

    def get_position(self, symbol: str) -> Optional[PositionDict]:
        return self.positions.get(str(symbol).upper())

    def update_position(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        entry_price: Optional[float] = None,
        **kwargs: Any,
    ) -> PositionDict:
        qty = kwargs.get("size", quantity)
        price = kwargs.get("price", entry_price)

        if qty is None:
            raise ValueError("quantity or size is required")
        if price is None:
            raise ValueError("entry_price or price is required")

        symbol = str(symbol).upper()
        qty = float(qty)
        price = float(price)

        position = PositionDict({
            "symbol": symbol,
            "side": str(getattr(side, "value", side)).upper(),
            "quantity": qty,
            "size": qty,
            "entry_price": price,
            "price": price,
            "sl": kwargs.get("sl", kwargs.get("stop_loss")),
            "tp": kwargs.get("tp", kwargs.get("take_profit")),
            "status": "OPEN",
            "updated_at": time.time(),
        })
        self.positions[symbol] = position
        return position

    def open_position(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        **kwargs: Any,
    ) -> PositionDict:
        return self.update_position(
            symbol=symbol,
            side=side,
            quantity=kwargs.get("size", quantity),
            entry_price=kwargs.get("entry_price", price),
            **kwargs,
        )

    def close_position(self, symbol: str, **kwargs: Any) -> Optional[PositionDict]:
        return self.positions.pop(str(symbol).upper(), None)
''',

"risk_manager.py": r'''from typing import Any, Optional, Tuple


class RiskConfig:
    def __init__(
        self,
        max_risk_per_trade_percent: float = 2.0,
        max_daily_loss_percent: float = 5.0,
        max_position_percent: float = 10.0,
        max_open_positions: int = 5,
        circuit_breaker_loss_pct: float = 10.0,
        **kwargs: Any,
    ) -> None:
        risk = kwargs.get(
            "risk_per_trade_pct",
            kwargs.get("max_risk_per_trade_pct", max_risk_per_trade_percent),
        )
        daily = kwargs.get("max_daily_loss_pct", max_daily_loss_percent)

        self.risk_per_trade_pct = float(risk)
        self.max_risk_per_trade_pct = float(risk)
        self.max_risk_per_trade_percent = float(risk)

        self.max_daily_loss_pct = float(daily)
        self.max_daily_loss_percent = float(daily)

        self.max_position_percent = float(
            kwargs.get("max_position_pct", max_position_percent)
        )
        self.max_open_positions = int(max_open_positions)
        self.circuit_breaker_loss_pct = float(circuit_breaker_loss_pct)

        # Aliasهای مورد استفاده در تست‌ها و Session
        self.stop_loss_pct = float(kwargs.get("stop_loss_pct", 0.0))
        self.take_profit_pct = float(kwargs.get("take_profit_pct", 0.0))
        self.min_trade_value = float(kwargs.get("min_trade_value", 0.0))


class RiskManager:
    def __init__(self, config: Optional[RiskConfig] = None, **kwargs: Any) -> None:
        self.config = config or RiskConfig(**kwargs)
        self.circuit_breaker_tripped = False
        self.daily_pnl = 0.0

    def validate_order(
        self,
        symbol: str,
        side: Any,
        quantity: float,
        price: float,
        **kwargs: Any,
    ) -> Tuple[bool, str]:
        if self.circuit_breaker_tripped:
            return False, "Circuit breaker is active"
        if float(quantity) <= 0:
            return False, "Quantity must be greater than zero"
        if float(price) <= 0:
            return False, "Price must be greater than zero"
        return True, "Order validated"
''',

"order_executor.py": r'''import time
from typing import Any, Dict, List, Optional

from src.core.order_manager import Order, OrderManager, OrderStatus, OrderType
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskManager


class OrderExecutor:
    def __init__(
        self,
        order_manager: Optional[OrderManager] = None,
        position_tracker: Optional[PositionTracker] = None,
        risk_manager: Optional[RiskManager] = None,
        **kwargs: Any,
    ) -> None:
        self.order_manager = order_manager or OrderManager()
        self.position_tracker = position_tracker or PositionTracker()
        self.risk_manager = risk_manager or RiskManager()

    def execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: float,
        price: Optional[float] = None,
        current_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Order:
        execution_price = current_price if current_price is not None else price
        if execution_price is None:
            raise ValueError("price or current_price is required")

        valid, reason = self.risk_manager.validate_order(
            symbol=symbol, side=side, quantity=quantity, price=float(execution_price)
        )
        if not valid:
            raise ValueError(reason)

        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=float(execution_price),
        )
        order.status = OrderStatus.FILLED.value
        order.filled_at = time.time()
        order.executed_price = float(execution_price)

        self.position_tracker.update_position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=float(execution_price),
            sl=kwargs.get("sl", stop_loss),
            tp=kwargs.get("tp", take_profit),
        )
        return order

    def place_and_execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        current_price: Optional[float] = None,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        qty = kwargs.get("size", quantity)
        if qty is None:
            raise ValueError("quantity or size is required")

        execution_price = current_price if current_price is not None else price
        order = self.execute_market_order(
            symbol=symbol,
            side=side,
            quantity=float(qty),
            price=execution_price,
            stop_loss=sl if sl is not None else stop_loss,
            take_profit=tp if tp is not None else take_profit,
        )
        position = self.position_tracker.get_position(symbol)

        return {
            "order": order.to_dict(),
            "position": position,
            "status": OrderStatus.FILLED.value,
        }

    def process_limit_orders(
        self,
        current_market_prices: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> List[Order]:
        prices = current_market_prices or kwargs.get("market_prices", {})
        triggered: List[Order] = []

        for order in list(self.order_manager.orders.values()):
            if order.order_type != OrderType.LIMIT.value:
                continue
            if order.status != OrderStatus.OPEN.value:
                continue

            market_price = prices.get(order.symbol)
            if market_price is None:
                continue

            market_price = float(market_price)
            should_fill = (
                (order.side == "BUY" and market_price <= order.price)
                or (order.side == "SELL" and market_price >= order.price)
            )
            if not should_fill:
                continue

            order.status = OrderStatus.FILLED.value
            order.filled_at = time.time()
            order.executed_price = market_price

            self.position_tracker.update_position(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                entry_price=order.price,
            )
            triggered.append(order)

        return triggered
''',

"paper_session.py": r'''from typing import Any, Dict, Optional

from src.core.order_executor import OrderExecutor
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskConfig, RiskManager


class PaperTradingSession:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        risk_config: Optional[RiskConfig] = None,
        order_executor: Optional[OrderExecutor] = None,
        position_tracker: Optional[PositionTracker] = None,
        **kwargs: Any,
    ) -> None:
        self.initial_balance = float(initial_balance)
        self.balance = float(initial_balance)
        self.risk_config = risk_config or RiskConfig(**kwargs)
        self.risk_manager = RiskManager(self.risk_config)
        self.position_tracker = position_tracker or PositionTracker()
        self.order_executor = order_executor or OrderExecutor(
            position_tracker=self.position_tracker,
            risk_manager=self.risk_manager,
        )
        self.market_prices: Dict[str, float] = {}

    def get_balance(self) -> float:
        return float(self.balance)

    def get_equity(self) -> float:
        position_value = 0.0
        for symbol, position in self.position_tracker.positions.items():
            quantity = float(position.get("quantity", position.get("size", 0.0)))
            entry = float(position.get("entry_price", 0.0))
            market = float(self.market_prices.get(symbol, entry))

            if position.get("side", "BUY") == "SELL":
                # ارزش اقتصادی Short = وثیقه اولیه + سود/زیان آن
                position_value += quantity * entry + quantity * (entry - market)
            else:
                position_value += quantity * market

        return float(self.balance + position_value)

    def update_market_prices(self, prices: Dict[str, float]) -> None:
        for symbol, price in prices.items():
            self.market_prices[str(symbol).upper()] = float(price)

    def execute_order(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        qty = kwargs.get("size", quantity)
        if qty is None or price is None:
            raise ValueError("quantity/size and price are required")

        qty = float(qty)
        price = float(price)
        side_value = str(getattr(side, "value", side)).upper()

        # در خرید، مبلغ سفارش از موجودی نقدی کسر می‌شود.
        if side_value == "BUY":
            self.balance -= qty * price

        self.market_prices[str(symbol).upper()] = price
        return self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=side_value,
            quantity=qty,
            current_price=price,
            sl=sl,
            tp=tp,
        )
''',

"integrated_pipeline.py": r'''from typing import Any, Callable, Dict, Optional

from src.core.order_executor import OrderExecutor
from src.core.order_manager import OrderManager
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskConfig, RiskManager


class IntegratedTradingPipeline:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        strategy: Optional[Callable[..., Dict[str, Any]]] = None,
        risk_config: Optional[RiskConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.initial_balance = float(initial_balance)
        self.strategy = strategy
        self.risk_manager = RiskManager(risk_config)
        self.position_tracker = PositionTracker()
        self.order_manager = OrderManager()
        self.order_executor = OrderExecutor(
            order_manager=self.order_manager,
            position_tracker=self.position_tracker,
            risk_manager=self.risk_manager,
        )

    def process_tick(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.step(market_data)

    def step(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.risk_manager.circuit_breaker_tripped:
            return {
                "action": "HOLD",
                "blocked": True,
                "reason": "Circuit breaker active",
            }

        signal: Dict[str, Any] = {}
        if callable(self.strategy):
            result = self.strategy(market_data)
            if isinstance(result, dict):
                signal = result
        else:
            for value in market_data.values():
                if isinstance(value, dict) and "action" in value:
                    signal = value
                    break

        action = str(signal.get("action", "HOLD")).upper()
        if action not in {"BUY", "SELL"}:
            return {"action": "HOLD", "status": "SKIPPED"}

        symbol = str(signal.get("symbol", "BTCUSDT")).upper()
        quantity = float(signal.get("quantity", signal.get("size", 0.1)))

        tick = market_data.get(symbol, {})
        if not isinstance(tick, dict):
            tick = {}

        price = float(
            signal.get("price", tick.get("close", tick.get("price", 0.0)))
        )
        if price <= 0:
            return {
                "action": "HOLD",
                "status": "SKIPPED",
                "reason": "No valid market price",
            }

        result = self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=action,
            quantity=quantity,
            current_price=price,
            sl=signal.get("sl"),
            tp=signal.get("tp"),
        )
        return {
            "action": action,
            "order": result["order"],
            "position": result["position"],
            "status": "EXECUTED",
        }
''',
}

print("[2/5] Writing direct source fixes...")
for filename, content in files.items():
    (CORE / filename).write_text(content.rstrip() + "\n", encoding="utf-8")

print("[3/5] Python syntax check...")
compile_result = subprocess.run(
    [sys.executable, "-m", "py_compile", *[str(CORE / name) for name in targets]],
    text=True,
)
if compile_result.returncode != 0:
    print(f"SYNTAX ERROR. Restoring backup from: {backup}")
    for name in targets:
        saved = backup / name
        if saved.exists():
            shutil.copy2(saved, CORE / name)
    raise SystemExit(1)

print("[4/5] Running the 7 failing tests only...")
focused = [
    "tests/test_order_manager.py",
    "tests/test_order_executor.py",
    "tests/test_paper_session.py",
    "tests/test_position_tracker.py",
    "tests/test_integrated_pipeline.py",
]
result1 = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", *focused],
    cwd=ROOT,
)

print("[5/5] Running full test suite...")
result2 = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "tests"],
    cwd=ROOT,
)

if result2.returncode == 0:
    print("\nSUCCESS: ALL TESTS PASSED.")
    print(f"Backup retained at: {backup}")
else:
    print("\nFAILED: Files were intentionally NOT auto-restored.")
    print("Reason: full pytest output is needed to fix any remaining real incompatibility.")
    print(f"Safe backup is available at: {backup}")
    raise SystemExit(result2.returncode)
