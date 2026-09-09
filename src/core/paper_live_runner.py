"""
AtriaTrade Paper Trading Live Runner
Single Source of Truth Execution Engine for Virtual/Paper Trading.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

from src.core.order_manager import Order, OrderSide, OrderType, OrderStatus
from src.core.portfolio_manager import PortfolioManager
from src.core.market_regime import MarketRegimeFilter as MarketRegimeEngine
from src.core.circuit_breaker import CircuitBreaker

logger = logging.getLogger("AtriaTrade.PaperRunner")


@dataclass
class PaperTradeSession:
    session_id: str
    initial_balance: float = 10000.0
    current_balance: float = 10000.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trades_count: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class PaperTradingLiveRunner:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        risk_per_trade_pct: float = 0.01,
        max_drawdown_limit_pct: float = 0.05,
    ):
        self.session = PaperTradeSession(
            session_id=f"paper_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            initial_balance=initial_balance,
            current_balance=initial_balance,
        )
        self.portfolio_manager = PortfolioManager(initial_balance=initial_balance)
        self.circuit_breaker = CircuitBreaker(max_drawdown_pct_halt=max_drawdown_limit_pct)
        self.regime_engine = MarketRegimeEngine()
        self.risk_per_trade_pct = risk_per_trade_pct
        self.trade_history: List[Dict[str, Any]] = []

    def process_candle(self, symbol: str, candle: Dict[str, float]) -> Optional[Order]:
        """
        Processes an incoming candle:
        1. Checks circuit breaker.
        2. Detects market regime.
        3. Evaluates positions.
        """
        close_price = candle.get("close", 0.0)
        
        if close_price <= 0:
            return None

        current_equity = self.session.current_balance + self.session.unrealized_pnl
        if self.circuit_breaker.is_halted:
            logger.warning("Circuit breaker tripped! Trading halted for paper session.")
            return None

        # Detect regime
        regime = self.regime_engine.detect_regime([candle])
        return None

    def execute_paper_order(
        self,
        symbol: str,
        side: OrderSide,
        price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[Order]:
        """
        Executes a simulated paper order and syncs with the single source of truth balance.
        """
        notional = price * quantity
        if notional > self.session.current_balance and side in (OrderSide.BUY, "BUY"):
            logger.warning(f"Insufficient funds: {notional} > {self.session.current_balance}")
            return None

        order_id = f"paper_ord_{len(self.trade_history) + 1}"
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side.value if isinstance(side, OrderSide) else side,
            order_type=OrderType.MARKET.value,
            quantity=quantity,
            price=price,
            status=OrderStatus.FILLED.value,
        )

        side_val = side.value if isinstance(side, OrderSide) else side
        if side_val == "BUY":
            self.session.current_balance -= notional
        elif side_val == "SELL":
            self.session.current_balance += notional

        self.session.trades_count += 1
        self.trade_history.append({
            "order_id": order_id,
            "symbol": symbol,
            "side": side_val,
            "price": price,
            "quantity": quantity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        })
        return order

    def get_session_summary(self) -> Dict[str, Any]:
        """Returns comprehensive real-time metrics of the paper session."""
        equity = self.session.current_balance + self.session.unrealized_pnl
        roi_pct = ((equity - self.session.initial_balance) / self.session.initial_balance) * 100
        return {
            "session_id": self.session.session_id,
            "initial_balance": self.session.initial_balance,
            "current_balance": self.session.current_balance,
            "equity": equity,
            "realized_pnl": self.session.realized_pnl,
            "unrealized_pnl": self.session.unrealized_pnl,
            "roi_pct": round(roi_pct, 2),
            "trades_count": self.session.trades_count,
            "is_active": self.session.is_active,
        }
