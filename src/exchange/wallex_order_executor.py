import uuid
import time
from typing import Dict, Any, Optional

try:
    from src.exchange.wallex_live_client import WallexLiveClient  # noqa: F401
except Exception:
    WallexLiveClient = None  # type: ignore

try:
    from src.core.risk_guard import WallexRiskGuard
except Exception:
    WallexRiskGuard = None  # type: ignore

try:
    from src.exchange.wallex_live_guard import WallexLiveGuard
except Exception:
    WallexLiveGuard = None  # type: ignore


class WallexOrderExecutor:
    """
    Order execution layer for Wallex exchange.
    Supports BUY / SELL market & limit orders.
    Safe by default: dry_run=True -> no real HTTP call.
    """

    VALID_SIDES = ("BUY", "SELL")
    VALID_TYPES = ("MARKET", "LIMIT")
    MAX_SAFETY_NOTIONAL_TMN = 20_000_000.0

    def __init__(
        self,
        client: Optional[Any] = None,
        dry_run: bool = True,
        min_notional_tmn: float = 100000.0,
        risk_guard: Optional[Any] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        **kwargs
    ):
        self.client = client
        self.dry_run = dry_run
        self.min_notional_tmn = float(min_notional_tmn)
        self.risk_guard = risk_guard
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.live_guard = WallexLiveGuard(api_key=self.api_key, api_secret=self.api_secret) if WallexLiveGuard else None

    # --- Stage 15 & 16 Contract ---
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float
    ) -> Dict[str, Any]:
        # Stage 16 Guard verification
        if not self.dry_run and self.live_guard:
            self.live_guard.verify_order_placement(dry_run=self.dry_run)

        # Stage 15 validation
        side_u = str(side).upper().strip()
        if side_u not in self.VALID_SIDES:
            return {"success": False, "reason": "INVALID_SIDE"}

        try:
            px = float(price)
            qty = float(quantity)
        except Exception:
            return {"success": False, "reason": "INVALID_PARAMS"}

        notional = px * qty
        if notional < self.min_notional_tmn:
            return {"success": False, "reason": "ORDER_BELOW_MIN_VALUE"}

        if notional > self.MAX_SAFETY_NOTIONAL_TMN:
            return {"success": False, "reason": "ORDER_EXCEEDS_SAFETY_LIMIT"}

        if self.dry_run:
            return {
                "success": True,
                "status": "SIMULATED_FILLED",
                "mode": "DRY_RUN",
                "order_id": f"DRY-{uuid.uuid4().hex[:12]}",
                "symbol": symbol,
                "side": side_u,
                "price": px,
                "quantity": qty,
                "notional": notional
            }

        return self.submit_order(symbol=symbol, side=side_u, order_type="LIMIT", quantity=qty, price=px)

    # --- Stage 23 & 25 Contract ---
    def validate_order(
        self,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
    ) -> Dict[str, Any]:
        try:
            side_u = str(side).upper().strip()
        except Exception:
            side_u = ""

        try:
            type_u = str(order_type).upper().strip()
        except Exception:
            type_u = ""

        if side_u not in self.VALID_SIDES:
            return {"ok": False, "reason": "INVALID_SIDE"}

        if type_u not in self.VALID_TYPES:
            return {"ok": False, "reason": "INVALID_ORDER_TYPE"}

        try:
            qty = float(quantity)
        except Exception:
            return {"ok": False, "reason": "INVALID_QUANTITY"}

        if qty <= 0:
            return {"ok": False, "reason": "NON_POSITIVE_QUANTITY"}

        if type_u == "LIMIT" and price is None:
            return {"ok": False, "reason": "LIMIT_PRICE_REQUIRED"}

        px = None
        if price is not None:
            try:
                px = float(price)
            except Exception:
                return {"ok": False, "reason": "INVALID_PRICE"}
            if px <= 0:
                return {"ok": False, "reason": "NON_POSITIVE_PRICE"}

        notional = (px * qty) if px is not None else 0.0

        if type_u == "LIMIT" and notional < self.min_notional_tmn:
            return {
                "ok": False,
                "reason": "BELOW_MIN_NOTIONAL",
                "notional": notional,
                "min_required": self.min_notional_tmn,
            }

        return {
            "ok": True,
            "side": side_u,
            "order_type": type_u,
            "quantity": qty,
            "price": px,
            "notional": notional,
        }

    def submit_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        check = self.validate_order(side=side, order_type=order_type, quantity=quantity, price=price)
        if not check.get("ok"):
            return {"success": False, "stage": "validation", **check}

        payload = {
            "symbol": str(symbol).upper().strip(),
            "side": check["side"],
            "type": check["order_type"],
            "quantity": check["quantity"],
        }
        if check["order_type"] == "LIMIT":
            payload["price"] = check["price"]

        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "order_id": f"DRY-{uuid.uuid4().hex[:12]}",
                "payload": payload,
                "timestamp": int(time.time()),
            }

        if self.client is None:
            return {"success": False, "stage": "execution", "reason": "NO_CLIENT"}

        try:
            resp = self.client.place_order(payload)
            if not isinstance(resp, dict):
                return {"success": False, "stage": "execution", "reason": "BAD_RESPONSE"}
            resp.setdefault("dry_run", False)
            return resp
        except Exception as exc:
            return {"success": False, "stage": "execution", "reason": str(exc)}

    def submit_order_with_risk_guard(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
        capital_tmn: float,
        stop_loss_price: float,
    ) -> Dict[str, Any]:
        check = self.validate_order(side=side, order_type=order_type, quantity=quantity, price=price)
        if not check.get("ok"):
            return {"success": False, "stage": "validation", **check}

        if self.risk_guard is None:
            return {"success": False, "stage": "risk", "reason": "NO_RISK_GUARD"}

        entry_price = check["price"]
        if entry_price is None:
            return {"success": False, "stage": "risk", "reason": "MISSING_ENTRY_PRICE"}

        verdict = self.risk_guard.evaluate_order(
            capital=float(capital_tmn),
            entry_price=float(entry_price),
            stop_loss_price=float(stop_loss_price),
            quantity=float(check["quantity"]),
            side=str(check["side"]),
        )

        if not verdict.get("allowed"):
            return {
                "success": False,
                "stage": "risk",
                "reason": verdict.get("reason", "RISK_REJECTED"),
                "details": verdict,
            }

        out = self.submit_order(
            symbol=symbol,
            side=check["side"],
            order_type=check["order_type"],
            quantity=check["quantity"],
            price=check["price"],
        )
        if isinstance(out, dict):
            out.setdefault("risk", verdict)
        return out
