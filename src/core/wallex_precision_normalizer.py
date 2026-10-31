import math
import logging
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("AtriaTrade.WallexPrecisionNormalizer")

@dataclass
class NormalizedOrderSpec:
    symbol: str
    is_valid: bool
    normalized_quantity: float
    normalized_price: Optional[float]
    notional_value: float = 0.0
    rejection_reason: Optional[str] = None

class WallexPrecisionNormalizer:
    """
    Normalizes order price and quantity to conform to Wallex step size, 
    tick size, and minimum notional value constraints.
    """

    @staticmethod
    def _round_to_step(value: float, step: float, rounding_mode=ROUND_DOWN) -> float:
        d_val = Decimal(str(value))
        d_step = Decimal(str(step))
        quotient = (d_val / d_step).quantize(Decimal('1'), rounding=rounding_mode)
        result = quotient * d_step
        return float(result)

    def normalize(
        self,
        symbol: str,
        raw_quantity: float,
        raw_price: Optional[float] = None,
        step_size: float = 0.0001,
        tick_size: float = 0.01,
        min_qty: Optional[float] = None,
        min_notional: float = 1.0
    ) -> NormalizedOrderSpec:
        effective_min_qty = min_qty if min_qty is not None else step_size

        if raw_quantity <= 0:
            return NormalizedOrderSpec(
                symbol=symbol,
                is_valid=False,
                normalized_quantity=0.0,
                normalized_price=raw_price,
                rejection_reason="QUANTITY_ZERO_OR_NEGATIVE"
            )

        # Quantity must always be rounded down to prevent insufficient balance errors
        norm_qty = self._round_to_step(raw_quantity, step_size, rounding_mode=ROUND_DOWN)

        if norm_qty < effective_min_qty:
            logger.warning(f"Normalized quantity {norm_qty} < min_qty {effective_min_qty} for {symbol}")
            return NormalizedOrderSpec(
                symbol=symbol,
                is_valid=False,
                normalized_quantity=0.0,
                normalized_price=raw_price,
                rejection_reason="QUANTITY_BELOW_MINIMUM"
            )

        norm_price = None
        if raw_price is not None and raw_price > 0:
            norm_price = self._round_to_step(raw_price, tick_size, rounding_mode=ROUND_HALF_UP)
            notional = norm_qty * norm_price
            if notional < min_notional:
                logger.warning(f"Notional value {notional:.2f} < min_notional {min_notional:.2f} for {symbol}")
                return NormalizedOrderSpec(
                    symbol=symbol,
                    is_valid=False,
                    normalized_quantity=norm_qty,
                    normalized_price=norm_price,
                    notional_value=notional,
                    rejection_reason="NOTIONAL_BELOW_MINIMUM"
                )
        else:
            notional = 0.0

        return NormalizedOrderSpec(
            symbol=symbol,
            is_valid=True,
            normalized_quantity=norm_qty,
            normalized_price=norm_price,
            notional_value=notional,
            rejection_reason=None
        )
