import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AtriaTrade.WallexLiveOrchestrator")


class WallexLiveOrchestrator:
    def __init__(
        self,
        execution_engine: Optional[Any] = None,
        heartbeat_monitor: Optional[Any] = None,
        rate_limiter: Optional[Any] = None,
        reconciler: Optional[Any] = None,
        *,
        adapter: Optional[Any] = None,
        capital_manager: Optional[Any] = None,
        **kwargs
    ):
        self.engine = execution_engine
        self.heartbeat = heartbeat_monitor
        self.limiter = rate_limiter
        self.reconciler = reconciler
        self.adapter = adapter
        self.capital_manager = capital_manager
        self.active_positions: Dict[str, Dict[str, Any]] = {}

    # --- Stage 10 Position Lifecycle Support ---
    def open_paper_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, Any]:
        pos = {
            "symbol": symbol,
            "side": side,
            "entry_price": float(entry_price),
            "quantity": float(quantity),
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "take_profit": float(take_profit) if take_profit is not None else None,
            "status": "OPEN",
        }
        self.active_positions[symbol] = pos
        return pos

    def _resolve_market_price(self, symbol: str) -> Optional[float]:
        if not self.adapter:
            return None

        # 1. Direct market_prices mapping (WallexPaperAdapter)
        if hasattr(self.adapter, "market_prices") and isinstance(self.adapter.market_prices, dict):
            if symbol in self.adapter.market_prices:
                return float(self.adapter.market_prices[symbol])
            sym_clean = symbol.replace("_", "").upper()
            if sym_clean in self.adapter.market_prices:
                return float(self.adapter.market_prices[sym_clean])

        # 2. get_ticker method
        if hasattr(self.adapter, "get_ticker") and callable(self.adapter.get_ticker):
            try:
                t = self.adapter.get_ticker(symbol)
                if isinstance(t, dict):
                    px = t.get("price") or t.get("lastPrice") or t.get("last")
                    if px is not None:
                        return float(px)
                elif isinstance(t, (int, float)):
                    return float(t)
            except Exception:
                pass

        # 3. get_market_price method
        if hasattr(self.adapter, "get_market_price") and callable(self.adapter.get_market_price):
            try:
                px = self.adapter.get_market_price(symbol)
                if px is not None:
                    return float(px)
            except Exception:
                pass

        # 4. generic prices attribute
        if hasattr(self.adapter, "prices") and isinstance(self.adapter.prices, dict):
            if symbol in self.adapter.prices:
                return float(self.adapter.prices[symbol])

        return None

    def process_tick(self, symbol: str) -> Dict[str, Any]:
        pos = self.active_positions.get(symbol)
        if not pos or pos.get("status") != "OPEN":
            return {"status": "NO_POSITION"}

        current_price = self._resolve_market_price(symbol)
        if current_price is None:
            return {"status": "OPEN", "price": None}

        entry_px = pos["entry_price"]
        qty = pos["quantity"]
        tp = pos.get("take_profit")
        sl = pos.get("stop_loss")
        side = pos.get("side", "BUY")

        # Check Take Profit & Stop Loss
        hit_tp = (side == "BUY" and tp is not None and current_price >= tp) or \
                 (side == "SELL" and tp is not None and current_price <= tp)
        hit_sl = (side == "BUY" and sl is not None and current_price <= sl) or \
                 (side == "SELL" and sl is not None and current_price >= sl)

        if hit_tp or hit_sl:
            pos["status"] = "CLOSED"
            exit_reason = "TAKE_PROFIT" if hit_tp else "STOP_LOSS"
            pos["exit_reason"] = exit_reason
            pnl = (current_price - entry_px) * qty if side == "BUY" else (entry_px - current_price) * qty
            pos["pnl"] = pnl
            return {
                "status": "CLOSED",
                "exit_reason": exit_reason,
                "exit_price": current_price,
                "pnl": pnl
            }

        return {"status": "OPEN", "price": current_price}

    # --- Stage 35 Live Pipeline Support ---
    def pre_flight_check(self) -> Dict[str, Any]:
        if self.limiter and not self.limiter.acquire(1.0):
            logger.warning("Pre-flight rejected: rate limit reached")
            return {"ready": False, "reason": "rate_limited"}

        if self.heartbeat:
            beat = self.heartbeat.ping()
            if not beat.get("is_healthy", False) or self.heartbeat.should_pause_trading():
                logger.error(f"Pre-flight rejected: heartbeat unhealthy ({beat.get('reason')})")
                return {"ready": False, "reason": "network_unhealthy", "heartbeat": beat}
            return {"ready": True, "reason": "ok", "latency_ms": beat.get("latency_ms", 0.0)}

        return {"ready": True, "reason": "ok", "latency_ms": 0.0}

    def execute_live_cycle(
        self,
        symbol: str,
        signal: Dict[str, Any],
        active_order_ids: List[str]
    ) -> Dict[str, Any]:
        check = self.pre_flight_check()
        if not check["ready"]:
            return {"status": "skipped", "reason": check["reason"]}

        recon = {}
        if self.reconciler:
            recon = self.reconciler.reconcile_open_orders(symbol=symbol, internal_order_ids=active_order_ids)
            if recon.get("orphan_orders"):
                logger.warning(f"Detected orphan orders: {recon['orphan_orders']}. Cancelling...")
                self.reconciler.cancel_orphan_orders(symbol=symbol, orphan_ids=recon["orphan_orders"])

        if signal and signal.get("action") in ("BUY", "SELL") and self.engine:
            exec_res = self.engine.execute_order(
                symbol=symbol,
                side=signal["action"],
                amount=signal.get("amount", 0.0),
                price=signal.get("price", 0.0)
            )
            return {
                "status": "executed",
                "execution": exec_res,
                "reconciliation": recon
            }

        return {"status": "idle", "reconciliation": recon}
