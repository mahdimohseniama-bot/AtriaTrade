import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("AtriaTrade.WallexOrderExecutor")


class WallexOrderExecutor:
    """Wallex order executor with layered safety guards.

    Guard order (MUST NOT be reordered):
      1) Kill switch   -> blocks everything (dry-run and live alike).
      2) dry_run=True  -> simulated fill, no API credentials required.
      3) dry_run=False -> requires ALLOW_WALLEX_LIVE=1 + API credentials.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        dry_run: bool = True,
        kill_switch: bool = False,
        **kwargs: Any,
    ) -> None:
        self.api_key = api_key or os.getenv("WALLEX_API_KEY")
        self.api_secret = api_secret or os.getenv("WALLEX_API_SECRET")
        self.dry_run = bool(dry_run)
        self.kill_switch = bool(kill_switch)
        self._sim_counter = 0

    # ------------------------------------------------------------- guards
    def _kill_switch_active(self) -> bool:
        return os.getenv("WALLEX_KILL_SWITCH", "0") == "1" or self.kill_switch

    def _live_env_ready(self) -> bool:
        allow_live = os.getenv("ALLOW_WALLEX_LIVE", "0") == "1"
        key = self.api_key or os.getenv("WALLEX_API_KEY")
        sec = self.api_secret or os.getenv("WALLEX_API_SECRET")
        return bool(allow_live and key and sec)

    def _validate_order(self, symbol: str, side: str, price: float, quantity: float) -> None:
        if not symbol or not str(symbol).strip():
            raise ValueError("symbol is required")
        if str(side).upper() not in ("BUY", "SELL"):
            raise ValueError("invalid side: %s" % side)
        if float(price) <= 0:
            raise ValueError("limit price must be positive")
        if float(quantity) <= 0:
            raise ValueError("quantity must be positive")

    # ------------------------------------------------------------- orders
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # 1) kill switch first - always
        if self._kill_switch_active():
            raise RuntimeError("LIVE_BLOCKED: Kill switch is active")

        self._validate_order(symbol, side, price, quantity)

        symbol = str(symbol).upper()
        side = str(side).upper()

        # 2) simulation path - zero API dependency
        if self.dry_run:
            self._sim_counter += 1
            order_id = "dry_run_order_%05d" % self._sim_counter
            notional = float(price) * float(quantity)
            logger.info(
                "[DRY_RUN] simulated %s %s qty=%s @ %s (notional=%s)",
                side, symbol, quantity, price, notional,
            )
            return {
                "status": "success",
                "mode": "dry_run",
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "price": float(price),
                "quantity": float(quantity),
                "notional": notional,
                "filled_quantity": float(quantity),
                "remaining_quantity": 0.0,
            }

        # 3) live path - hard gate
        if not self._live_env_ready():
            raise RuntimeError(
                "LIVE_BLOCKED: Live trading environment not verified or allowed"
            )

        raise NotImplementedError(
            "Live Wallex order placement is not wired yet; "
            "complete the live signing layer before enabling."
        )
