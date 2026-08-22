from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


"
    position_size:Decision:
    allow_trade: bool
    reason: str = "ok"
    position_size: float = 0.0
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    trailing_stop_price: Optional[float] = None


@dataclass
class RiskConfig:
    # Capital / allocation
    risk_per_trade_pct: float = 1.0          # 1% of active capital per trade
    max_position_pct: float = 10.0           # Max 10% of active capital in one position

    # Loss control
    max_daily_loss_pct: float = 3.0          # Stop trading for the day after 3% loss
    max_drawdown_pct: float = 15.0           # Stop trading if peak-to-trough loss exceeds 15%
    max_consecutive_losses: int = 3          # Stop after 3 losing trades in a row

    # Stop / target logic
    stop_loss_pct: float = 1.5               # Default stop loss from entry
    take_profit_pct: float = 3.0             # Default take profit from entry
    trailing_stop_pct: float = 1.0           # Trailing stop distance from peak price

    # Safety
    min_trade_value: float = 10.0            # Do not open tiny trades
    fee_buffer_pct: float = 0.2              # Reserve small buffer for fees/slippage


@dataclass
class RiskState:
    peak_equity: float = 0.0
    day_start_equity: float = 0.0
    consecutive_losses: int = 0
    halted: bool = False
    halt_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskManager:
    """
    Risk manager for paper trading / backtesting only.

    Responsibilities:
    - position sizing
    - stop-loss / take-profit calculation
    - trailing stop calculation
    - daily loss limit check
    - max drawdown check
    - consecutive loss halt check
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.state = RiskState()

    def initialize_equity(self, current_equity: float) -> None:
        """
        Call once at start of a session/day.
        """
        self.state.day_start_equity = float(current_equity)
        self.state.peak_equity = float(current_equity)
        self.state.halted = False
        self.state.halt_reason = ""
        self.state.consecutive_losses = 0

    def update_equity(self, current_equity: float) -> None:
        """
        Update peak equity and re-check drawdown.
        """
        current_equity = float(current_equity)

        if current_equity > self.state.peak_equity:
            self.state.peak_equity = current_equity

        self._check_drawdown(current_equity)

    def register_trade_result(self, pnl: float) -> None:
        """
        Register the outcome of a closed trade.
        Positive pnl resets consecutive loss counter.
        Negative pnl increments it.
        """
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0

        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            self.state.halted = True
            self.state.halt_reason = (
                f"max_consecutive_losses reached ({self.state.consecutive_losses})"
            )

    def can_trade(self, current_equity: float) -> RiskDecision:
        """
        Returns whether a new trade is allowed.
        """
        current_equity = float(current_equity)

        if current_equity <= 0:
            return RiskDecision(
                allow_trade=False,
                reason="invalid_equity"
            )

        if self.state.halted:
            return RiskDecision(
                allow_trade=False,
                reason=self.state.halt_reason or "risk_halted"
            )

        # Ensure day start equity exists
        if self.state.day_start_equity <= 0:
            self.initialize_equity(current_equity)

        # Daily loss check
        daily_loss_pct = self._percent_loss(self.state.day_start_equity, current_equity)
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            self.state.halted = True
            self.state.halt_reason = f"max_daily_loss reached ({daily_loss_pct:.2f}%)"
            return RiskDecision(allow_trade=False, reason=self.state.halt_reason)

        # Drawdown check
        if self.state.peak_equity > 0:
            drawdown_pct = self._percent_loss(self.state.peak_equity, current_equity)
            if drawdown_pct >= self.config.max_drawdown_pct:
                self.state.halted = True
                self.state.halt_reason = f"max_drawdown reached ({drawdown_pct:.2f}%)"
                return RiskDecision(allow_trade=False, reason=self.state.halt_reason)

        # Consecutive losses check
        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            self.state.halted = True
            self.state.halt_reason = (
                f"max_consecutive_losses reached ({self.state.consecutive_losses})"
            )
            return RiskDecision(allow_trade=False, reason=self.state.halt_reason)

        return RiskDecision(allow_trade=True, reason="ok")

    def calculate_position_size(
        self,
        current_equity: float,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
    ) -> float:
        """
        Calculate position size in units of the asset.

        The size is based on:
        - risk per trade
        - max position cap
        - minimum trade value
        """
        current_equity = float(current_equity)
        entry_price = float(entry_price)

        if current_equity <= 0 or entry_price <= 0:
            return 0.0

        risk_budget = current_equity * (self.config.risk_per_trade_pct / 100.0)

        if stop_loss_price is not None and stop_loss_price > 0:
            stop_distance = abs(entry_price - float(stop_loss_price))
        else:
            stop_distance = entry_price * (self.config.stop_loss_pct / 100.0)

        if stop_distance <= 0:
            return 0.0

        # Raw position size from risk budget
        raw_size = risk_budget / stop_distance

        # Cap by max position value
        max_position_value = current_equity * (self.config.max_position_pct / 100.0)
        max_size_by_cap = max_position_value / entry_price

        size = min(raw_size, max_size_by_cap)

        # Fee/slippage buffer reduction
        size *= (1.0 - self.config.fee_buffer_pct / 100.0)

        if size * entry_price < self.config.min_trade_value:
            return 0.0

        return max(size, 0.0)

    def calculate_exit_levels(
        self,
        entry_price: float,
        side: str = "buy",
    ) -> Dict[str, float]:
        """
        Calculate stop-loss, take-profit and trailing stop levels.
        Supports long-only logic for now.
        """
        entry_price = float(entry_price)
        if entry_price <= 0:
            return {}

        side = side.lower().strip()
        if side != "buy":
            raise ValueError("RiskManager currently supports long-only paper trading")

        stop_loss_price = entry_price * (1.0 - self.config.stop_loss_pct / 100.0)
        take_profit_price = entry_price * (1.0 + self.config.take_profit_pct / 100.0)
        trailing_stop_price = entry_price * (1.0 - self.config.trailing_stop_pct / 100.0)

        return {
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price,
            "trailing_stop_price": trailing_stop_price,
        }

    def update_trailing_stop(self, peak_price: float) -> Optional[float]:
        """
        Update trailing stop from the highest price seen.
        """
        peak_price = float(peak_price)
        if peak_price <= 0:
            return None

        return peak_price * (1.0 - self.config.trailing_stop_pct / 100.0)

    def _check_drawdown(self, current_equity: float) -> None:
        if self.state.peak_equity <= 0:
            return

        drawdown_pct = self._percent_loss(self.state.peak_equity, current_equity)
        if drawdown_pct >= self.config.max_drawdown_pct:
            self.state.halted = True
            self.state.halt_reason = f"max_drawdown reached ({drawdown_pct:.2f}%)"

    @staticmethod
    def _percent_loss(base: float, current: float) -> float:
        if base <= 0:
            return 0.0
        if current >= base:
            return 0.0
        return ((base - current) / base) * 100.0

    def reset_halt(self) -> None:
        """
        Manually reset risk halt state.
        Use only when starting a new session/day in paper trading.
        """
        self.state.halted = False
        self.state.halt_reason = ""
        self.state.consecutive_losses = 0

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a serializable snapshot of current risk state.
        """
        return {
            "config": {
                "risk_per_trade_pct": self.config.risk_per_trade_pct,
                "max_position_pct": self.config.max_position_pct,
                "max_daily_loss_pct": self.config.max_daily_loss_pct,
                "max_drawdown_pct": self.config.max_drawdown_pct,
                "max_consecutive_losses": self.config.max_consecutive_losses,
                "stop_loss_pct": self.config.stop_loss_pct,
                "take_profit_pct": self.configmin_trade_value": self.config.min_trade_stop_pct": self.config.trailing_stop_pct,
                "min_trade_value": self.config.min_trade_value,
                "fee_buffer_pct": self.config.fee_buffer_pct,
            },
            "state": {
                "peak_equity": self.state.peak_equity,
                "day_start_equity": self.state.day_start_equity,
                "consecutive_losses": self.state.consecutive_losses,
                "halted": self.state.halted,
                "halt_reason": self.state.halt_reason,
                "metadata": self.state.metadata,
            },
        }

