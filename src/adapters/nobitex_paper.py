"""Nobitex Paper / Sandbox Exchange Adapter for AtriaTrade."""

import time
import uuid
from typing import Dict, Any, Optional


class NobitexPaperAdapter:
    """
    Simulated Paper Trading Adapter for Nobitex Exchange.
    Handles virtual balances, order execution simulation, fees, and orderbook matching.
    """

    DEFAULT_FEES = {
        "maker": 0.002,  # 0.2%
        "taker": 0.0025  # 0.25%
    }

    def __init__(self, initial_balances: Optional[Dict[str, float]] = None):
        """Initialize adapter with paper trading virtual wallets."""
        self.wallets: Dict[str, float] = initial_balances or {
            "rls": 500_000_000.0,   # 50,000,000 Tomans
            "usdt": 1000.0,
            "btc": 0.05,
            "eth": 0.5
        }
        # Normalize wallet keys to lowercase
        self.wallets = {k.lower(): float(v) for k, v in self.wallets.items()}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.market_prices: Dict[str, float] = {
            "BTCIRT": 6_500_000_000.0,
            "USDTIRT": 65_000.0,
            "ETHIRT": 230_000_000.0,
            "BTCUSDT": 100_000.0,
            "ETHUSDT": 3_500.0
        }

    def normalize_symbol(self, symbol: str) -> str:
        """Standardize symbol notation (e.g. btc-irt or btcirt -> BTCIRT)."""
        return symbol.upper().replace("-", "").replace("_", "").replace("/", "")

    def set_market_price(self, symbol: str, price: float) -> None:
        """Helper to inject simulated current market price for testing/ticker."""
        sym = self.normalize_symbol(symbol)
        self.market_prices[sym] = float(price)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch simulated ticker information."""
        sym = self.normalize_symbol(symbol)
        price = self.market_prices.get(sym, 100.0)
        return {
            "symbol": sym,
            "last": price,
            "bid": price * 0.999,
            "ask": price * 1.001,
            "timestamp": int(time.time() * 1000)
        }

    def get_order_book(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch simulated order book."""
        ticker = self.get_ticker(symbol)
        mid_price = ticker["last"]
        bids = [[mid_price * (1 - 0.001 * i), 0.5 * (i + 1)] for i in range(1, limit + 1)]
        asks = [[mid_price * (1 + 0.001 * i), 0.5 * (i + 1)] for i in range(1, limit + 1)]
        return {
            "symbol": ticker["symbol"],
            "bids": bids,
            "asks": asks,
            "timestamp": int(time.time() * 1000)
        }

    def get_balance(self, currency: str) -> float:
        """Get virtual balance for a specific currency."""
        return self.wallets.get(currency.lower(), 0.0)

    def get_all_balances(self) -> Dict[str, float]:
        """Get all virtual balances."""
        return self.wallets.copy()

    def _split_symbol(self, symbol: str) -> tuple[str, str]:
        """Splits symbol into base and quote currencies."""
        sym = self.normalize_symbol(symbol)
        if sym.endswith("IRT") or sym.endswith("RLS"):
            return sym[:-3].lower(), "rls"
        elif sym.endswith("USDT"):
            return sym[:-4].lower(), "usdt"
        else:
            return sym[:3].lower(), sym[3:].lower()

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a simulated order on Nobitex Paper market.
        Validates sufficient balance, calculates fees, and executes.
        """
        sym = self.normalize_symbol(symbol)
        side_clean = side.lower()
        type_clean = order_type.lower()
        amount = float(amount)

        if amount <= 0:
            return {"status": "failed", "error": "Order amount must be greater than zero"}

        base_curr, quote_curr = self._split_symbol(sym)
        current_market_price = self.market_prices.get(sym, 100.0)
        exec_price = float(price) if (type_clean == "limit" and price is not None) else current_market_price

        order_value = amount * exec_price
        fee_rate = self.DEFAULT_FEES["taker"] if type_clean == "market" else self.DEFAULT_FEES["maker"]

        order_id = str(uuid.uuid4())[:12]

        if side_clean == "buy":
            total_required = order_value * (1.0 + fee_rate)
            available_quote = self.wallets.get(quote_curr, 0.0)
            if available_quote < total_required:
                return {
                    "status": "failed",
                    "error": f"Insufficient {quote_curr.upper()} balance. Required: {total_required:.2f}, Available: {available_quote:.2f}"
                }

            fee_amount = order_value * fee_rate
            self.wallets[quote_curr] -= total_required
            self.wallets[base_curr] = self.wallets.get(base_curr, 0.0) + amount

        elif side_clean == "sell":
            available_base = self.wallets.get(base_curr, 0.0)
            if available_base < amount:
                return {
                    "status": "failed",
                    "error": f"Insufficient {base_curr.upper()} balance. Required: {amount}, Available: {available_base}"
                }

            fee_amount = order_value * fee_rate
            net_proceeds = order_value - fee_amount
            self.wallets[base_curr] -= amount
            self.wallets[quote_curr] = self.wallets.get(quote_curr, 0.0) + net_proceeds

        else:
            return {"status": "failed", "error": f"Invalid order side: {side}"}

        order_record = {
            "order_id": order_id,
            "symbol": sym,
            "side": side_clean,
            "type": type_clean,
            "amount": amount,
            "price": exec_price,
            "fee": fee_amount,
            "fee_currency": quote_curr.upper(),
            "status": "FILLED",
            "timestamp": int(time.time() * 1000)
        }
        self.orders[order_id] = order_record
        return {"status": "success", "order": order_record}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an open order."""
        if order_id in self.orders:
            if self.orders[order_id]["status"] == "FILLED":
                return {"status": "failed", "error": "Cannot cancel already filled order"}
            self.orders[order_id]["status"] = "CANCELED"
            return {"status": "success", "message": f"Order {order_id} canceled"}
        return {"status": "failed", "error": "Order not found"}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Query status of a specific order."""
        if order_id in self.orders:
            return {"status": "success", "order": self.orders[order_id]}
        return {"status": "failed", "error": "Order not found"}
