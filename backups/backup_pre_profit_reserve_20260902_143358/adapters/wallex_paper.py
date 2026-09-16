"""Wallex Paper / Sandbox Exchange Adapter for AtriaTrade."""

import time
import uuid
from typing import Dict, Any, Optional


class WallexPaperAdapter:
    """
    Simulated Paper Trading Adapter for Wallex Exchange.
    Handles virtual balances, order execution simulation, fees (maker/taker),
    and market quote conversions (TM/USDT).
    """

    DEFAULT_FEES = {
        "maker": 0.002,  # 0.2%
        "taker": 0.0025  # 0.25%
    }

    def __init__(self, initial_balances: Optional[Dict[str, float]] = None):
        """Initialize adapter with paper trading virtual balances."""
        self.wallets: Dict[str, float] = initial_balances or {
            "tm": 50_000_000.0,   # 50,000,000 Tomans
            "usdt": 1000.0,
            "btc": 0.05,
            "eth": 0.5
        }
        self.wallets = {k.lower(): float(v) for k, v in self.wallets.items()}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.market_prices: Dict[str, float] = {
            "BTCTM": 6_500_000_000.0,
            "USDTTM": 65_000.0,
            "ETHTM": 230_000_000.0,
            "BTCUSDT": 100_000.0,
            "ETHUSDT": 3_500.0
        }

    def normalize_symbol(self, symbol: str) -> str:
        """Standardize symbol notation (e.g. btc-tm or btctm -> BTCTM)."""
        return symbol.upper().replace("-", "").replace("_", "").replace("/", "")

    def set_market_price(self, symbol: str, price: float) -> None:
        """Set simulated market price for testing."""
        sym = self.normalize_symbol(symbol)
        self.market_prices[sym] = float(price)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch simulated ticker data."""
        sym = self.normalize_symbol(symbol)
        price = self.market_prices.get(sym, 100.0)
        return {
            "symbol": sym,
            "lastPrice": price,
            "bidPrice": price * 0.999,
            "askPrice": price * 1.001,
            "timestamp": int(time.time() * 1000)
        }

    def get_order_book(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch simulated order book."""
        ticker = self.get_ticker(symbol)
        mid = ticker["lastPrice"]
        bids = [{"price": mid * (1 - 0.001 * i), "quantity": 0.5 * (i + 1)} for i in range(1, limit + 1)]
        asks = [{"price": mid * (1 + 0.001 * i), "quantity": 0.5 * (i + 1)} for i in range(1, limit + 1)]
        return {
            "symbol": ticker["symbol"],
            "bids": bids,
            "asks": asks,
            "timestamp": int(time.time() * 1000)
        }

    def get_balance(self, currency: str) -> float:
        """Get virtual balance for a specific asset."""
        return self.wallets.get(currency.lower(), 0.0)

    def get_all_balances(self) -> Dict[str, float]:
        """Get copy of all virtual wallet balances."""
        return self.wallets.copy()

    def _split_symbol(self, symbol: str) -> tuple[str, str]:
        """Split symbol into base and quote currencies."""
        sym = self.normalize_symbol(symbol)
        if sym.endswith("TM"):
            return sym[:-2].lower(), "tm"
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
        """Place simulated order on Wallex Paper market."""
        sym = self.normalize_symbol(symbol)
        side_clean = side.lower()
        type_clean = order_type.lower()
        amount = float(amount)

        if amount <= 0:
            return {"status": "failed", "error": "Order amount must be greater than zero"}

        base_curr, quote_curr = self._split_symbol(sym)
        current_price = self.market_prices.get(sym, 100.0)
        exec_price = float(price) if (type_clean == "limit" and price is not None) else current_price

        order_value = amount * exec_price
        fee_rate = self.DEFAULT_FEES["taker"] if type_clean == "market" else self.DEFAULT_FEES["maker"]
        order_id = f"wallex_{uuid.uuid4().hex[:10]}"

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
            "clientOrderId": order_id,
            "symbol": sym,
            "side": side_clean,
            "type": type_clean,
            "origQty": amount,
            "executedQty": amount,
            "price": exec_price,
            "fee": fee_amount,
            "feeAsset": quote_curr.upper(),
            "status": "FILLED",
            "timestamp": int(time.time() * 1000)
        }
        self.orders[order_id] = order_record
        return {"status": "success", "result": order_record}

    def cancel_order(self, client_order_id: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        if client_order_id in self.orders:
            if self.orders[client_order_id]["status"] == "FILLED":
                return {"status": "failed", "error": "Cannot cancel filled order"}
            self.orders[client_order_id]["status"] = "CANCELED"
            return {"status": "success", "message": "Order canceled"}
        return {"status": "failed", "error": "Order not found"}

    def get_order(self, client_order_id: str) -> Dict[str, Any]:
        """Get details of an order."""
        if client_order_id in self.orders:
            return {"status": "success", "result": self.orders[client_order_id]}
        return {"status": "failed", "error": "Order not found"}
