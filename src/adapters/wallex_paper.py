from typing import Dict, Any, Optional
import time
import uuid

class WallexPaperAdapter:
    """
    Paper trading adapter simulating Wallex exchange API.
    Fully compatible with PaperExchangeFactory and order lifecycle tests.
    """

    DEFAULT_BALANCES = {
        "tm": 50_000_000.0,
        "usdt": 1000.0,
        "btc": 0.05,
        "eth": 0.5,
    }

    DEFAULT_FEES = {
        "maker": 0.002,
        "taker": 0.0025,
    }

    def __init__(
        self,
        initial_balances: Optional[Dict[str, float]] = None,
        initial_balance: Optional[float] = None,
        symbol: str = "USDTTMN",
        **kwargs: Any
    ):
        self.symbol = symbol.upper().replace("-", "")
        if initial_balances is not None:
            self.wallets = {k.lower(): float(v) for k, v in initial_balances.items()}
        elif initial_balance is not None:
            self.wallets = dict(self.DEFAULT_BALANCES)
            self.wallets["tm"] = float(initial_balance)
            self.wallets["tmn"] = float(initial_balance)
            self.wallets["usdt"] = 0.0
        else:
            self.wallets = dict(self.DEFAULT_BALANCES)

        self.orders: Dict[str, Dict[str, Any]] = {}
        self.market_prices: Dict[str, float] = {
            "USDTTMN": 65_000.0,
            "USDTTM": 65_000.0,
            "BTCTMN": 6_500_000_000.0,
            "BTCTM": 6_500_000_000.0,
            "ETHTMN": 230_000_000.0,
            "ETHTM": 230_000_000.0,
            "BTCUSDT": 100_000.0,
            "ETHUSDT": 3500.0,
        }

    @property
    def balance(self) -> float:
        if "tmn" in self.wallets:
            return float(self.wallets["tmn"])
        if "tm" in self.wallets:
            return float(self.wallets["tm"])
        return float(self.wallets.get("rls", 0.0))

    @balance.setter
    def balance(self, val: float) -> None:
        self.wallets["tm"] = float(val)
        self.wallets["tmn"] = float(val)

    def get_balance(self, asset: str) -> float:
        k = asset.lower()
        if k in ("tm", "tmn"):
            return self.wallets.get("tm", self.wallets.get("tmn", 0.0))
        return float(self.wallets.get(k, 0.0))

    def get_balances(self) -> Dict[str, float]:
        return dict(self.wallets)

    def set_market_price(self, symbol: str, price: float) -> None:
        self.market_prices[symbol.upper().replace("-", "")] = float(price)

    def _split_symbol(self, symbol: str) -> tuple[str, str]:
        sym = symbol.upper().replace("-", "")
        if sym.endswith("TMN"):
            return sym[:-3].lower(), "tm"
        if sym.endswith("TM"):
            return sym[:-2].lower(), "tm"
        if sym.endswith("USDT"):
            return sym[:-4].lower(), "usdt"
        return sym[:-4].lower(), sym[-4:].lower()

    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        sym = (symbol or self.symbol).upper().replace("-", "")
        price = self.market_prices.get(sym, 65_000.0)
        return {
            "symbol": sym,
            "lastPrice": price,
            "bidPrice": price * 0.999,
            "askPrice": price * 1.001,
            "timestamp": int(time.time() * 1000),
        }

    def get_order_book(self, symbol: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        ticker = self.get_ticker(symbol)
        mid = ticker["lastPrice"]
        bids = [{"price": mid * (1 - 0.001 * i), "quantity": 0.5 * (i + 1)} for i in range(1, limit + 1)]
        asks = [{"price": mid * (1 + 0.001 * i), "quantity": 0.5 * (i + 1)} for i in range(1, limit + 1)]
        return {"bids": bids, "asks": asks}

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        base_asset, quote_asset = self._split_symbol(symbol)
        side_norm = side.upper()
        type_norm = order_type.upper()

        if amount <= 0:
            return {"status": "failed", "error": "Amount must be greater than zero"}

        exec_price = float(price) if (type_norm == "LIMIT" and price is not None) else self.market_prices.get(symbol.upper().replace("-", ""), 65_000.0)
        fee_rate = self.DEFAULT_FEES["maker"] if type_norm == "LIMIT" else self.DEFAULT_FEES["taker"]

        if side_norm == "BUY":
            gross_cost = float(amount) * exec_price
            fee = gross_cost * fee_rate
            total_required = gross_cost + fee
            quote_bal = self.get_balance(quote_asset)
            if quote_bal < total_required:
                return {
                    "status": "failed",
                    "error": f"Insufficient {quote_asset.upper()} balance. Required: {total_required}, Available: {quote_bal}",
                }
            self.wallets[quote_asset] = quote_bal - total_required
            if quote_asset in ("tm", "tmn"):
                self.wallets["tm"] = self.wallets[quote_asset]
                self.wallets["tmn"] = self.wallets[quote_asset]
            self.wallets[base_asset] = self.get_balance(base_asset) + float(amount)
            fee_asset = quote_asset
        elif side_norm == "SELL":
            base_bal = self.get_balance(base_asset)
            if base_bal < amount:
                return {
                    "status": "failed",
                    "error": f"Insufficient {base_asset.upper()} balance. Required: {amount}, Available: {base_bal}",
                }
            gross_proceeds = float(amount) * exec_price
            fee = gross_proceeds * fee_rate
            net_proceeds = gross_proceeds - fee
            self.wallets[base_asset] = base_bal - float(amount)
            self.wallets[quote_asset] = self.get_balance(quote_asset) + net_proceeds
            if quote_asset in ("tm", "tmn"):
                self.wallets["tm"] = self.wallets[quote_asset]
                self.wallets["tmn"] = self.wallets[quote_asset]
            fee_asset = quote_asset
        else:
            return {"status": "failed", "error": f"Invalid side: {side}"}

        order_id = f"wlx_paper_{uuid.uuid4().hex[:8]}"
        order_record = {
            "clientOrderId": order_id,
            "order_id": order_id,
            "symbol": symbol.upper().replace("-", ""),
            "side": side_norm,
            "type": type_norm,
            "price": exec_price,
            "amount": float(amount),
            "origQty": float(amount),
            "executedQty": float(amount),
            "qty": float(amount),
            "status": "FILLED",
            "fee": fee,
            "feeAsset": fee_asset,
            "time": int(time.time() * 1000),
        }
        self.orders[order_id] = order_record
        return {"status": "success", "result": order_record, "order": order_record}

    def execute_market_order(self, side: str, amount: float) -> Dict[str, Any]:
        side_norm = side.upper()
        ticker = self.get_ticker(self.symbol)
        curr_price = ticker["lastPrice"]
        base_asset, quote_asset = self._split_symbol(self.symbol)

        if side_norm == "BUY":
            if amount > 1000 and curr_price > 0:
                qty = amount / curr_price
            else:
                qty = amount
            res = self.place_order(symbol=self.symbol, side="BUY", order_type="MARKET", amount=qty)
        elif side_norm == "SELL":
            qty = amount
            if qty <= 0:
                qty = self.get_balance(base_asset)
            res = self.place_order(symbol=self.symbol, side="SELL", order_type="MARKET", amount=qty)
        else:
            return {"status": "REJECTED", "error": f"Invalid side: {side}"}

        if res.get("status") == "success":
            rec = res.get("result", {})
            return {
                "status": "FILLED",
                "order_id": rec.get("clientOrderId"),
                "symbol": rec.get("symbol"),
                "side": rec.get("side"),
                "price": rec.get("price"),
                "amount": rec.get("amount"),
                "origQty": rec.get("origQty"),
                "executedQty": rec.get("executedQty"),
                "qty": rec.get("executedQty"),
                "fee": rec.get("fee"),
                "result": rec,
                "order": rec,
            }
        return {"status": "REJECTED", "error": res.get("error", "Execution failed")}

    def cancel_order(self, client_order_id: str) -> Dict[str, Any]:
        if client_order_id not in self.orders:
            return {"status": "failed", "error": f"Order {client_order_id} not found"}
        order = self.orders[client_order_id]
        if order["status"] == "FILLED":
            return {"status": "failed", "error": f"Order {client_order_id} already FILLED"}
        order["status"] = "CANCELED"
        return {"status": "success", "result": order, "order": order}

    def get_order(self, client_order_id: str) -> Dict[str, Any]:
        if client_order_id not in self.orders:
            return {"status": "failed", "error": f"Order {client_order_id} not found"}
        return {"status": "success", "result": self.orders[client_order_id], "order": self.orders[client_order_id]}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return self.get_order(order_id)
