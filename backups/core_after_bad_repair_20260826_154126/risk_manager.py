from typing import Any, Optional, Tuple


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
