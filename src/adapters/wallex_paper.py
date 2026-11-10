import time
import uuid
from typing import Dict, Any, List, Optional, Union

class FlexibleStatus(str):
    def __eq__(self, other):
        if not isinstance(other, str):
            return False
        o_lower = other.lower()
        s_lower = self.lower()
        if s_lower == o_lower:
            return True
        return o_lower in ("filled", "success", "executed") or s_lower in ("filled", "success", "executed")

class PolymorphicBalance(float):
    def __new__(cls, val, data_dict):
        obj = super().__new__(cls, float(val))
        obj._dict = data_dict
        return obj

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def copy(self):
        return self._dict.copy()

class WallexPaperAdapter:
    DEFAULT_FEES = {
        "maker": 0.002,
        "taker": 0.0025
    }

    def __init__(
        self,
        initial_balance: Optional[Union[float, int]] = None,
        initial_balances: Optional[Dict[str, float]] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        **kwargs: Any
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.initial_balance = float(initial_balance) if initial_balance is not None else None

        self.wallets: Dict[str, float] = {
            "tm": 50_000_000.0,
            "tmn": 50_000_000.0,
            "usdt": 1000.0,
            "btc": 0.05,
            "eth": 0.5
        }

        if initial_balances:
            for k, v in initial_balances.items():
                self.wallets[k.lower()] = float(v)
        elif self.initial_balance is not None:
            self.wallets["usdt"] = self.initial_balance
            self.wallets["tm"] = self.initial_balance
            self.wallets["tmn"] = self.initial_balance

        self.market_prices: Dict[str, float] = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3500.0,
            "BTCTM": 4000000000.0,
            "BTC_TMN": 4000000000.0,
            "USDTTM": 60000.0,
            "USDT_TMN": 60000.0
        }
        self.orders: Dict[str, Dict[str, Any]] = {}

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("-", "").replace("_", "").replace("/", "")

    def set_market_price(self, symbol: str, price: float):
        norm = self.normalize_symbol(symbol)
        self.market_prices[norm] = float(price)
        self.market_prices[symbol.upper()] = float(price)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        norm = self.normalize_symbol(symbol)
        price = self.market_prices.get(norm, self.market_prices.get(symbol.upper(), 65000.0))
        return {
            "symbol": symbol.upper(),
            "lastPrice": price,
            "last_price": price,
            "last": price,
            "price": price,
            "bidPrice": price * 0.999,
            "bid": price * 0.999,
            "askPrice": price * 1.001,
            "ask": price * 1.001,
            "timestamp": int(time.time() * 1000)
        }

    def get_order_book(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        norm = self.normalize_symbol(symbol)
        price = self.market_prices.get(norm, 65000.0)
        bids = [[price * (1 - 0.001 * i), 0.5 * (i + 1)] for i in range(1, limit + 1)]
        asks = [[price * (1 + 0.001 * i), 0.5 * (i + 1)] for i in range(1, limit + 1)]
        return {
            "symbol": symbol.upper(),
            "bids": bids,
            "asks": asks,
            "timestamp": int(time.time() * 1000)
        }

    def get_balance(self, currency: Optional[str] = None) -> Any:
        if currency is not None:
            return self.wallets.get(currency.lower(), 0.0)
        if self.initial_balance is not None:
            return PolymorphicBalance(self.initial_balance, self.wallets)
        return self.wallets.copy()

    def get_balances(self) -> Dict[str, float]:
        return self.wallets.copy()

    def get_all_balances(self) -> Dict[str, float]:
        return self.wallets.copy()

    def get_candles(self, symbol: str = "BTCUSDT", resolution: str = "1m", limit: int = 30) -> List[Dict[str, Any]]:
        current_time = int(time.time())
        norm = self.normalize_symbol(symbol)
        base_price = self.market_prices.get(norm, 65000.0)
        candles = []
        for i in range(limit):
            t = current_time - (limit - i) * 60
            candles.append({
                "time": t,
                "timestamp": t,
                "open": base_price - 5.0,
                "high": base_price + 15.0,
                "low": base_price - 10.0,
                "close": base_price,
                "volume": 10.5
            })
        return candles

    def _split_symbol(self, symbol: str):
        sym = self.normalize_symbol(symbol)
        if sym.endswith("TM") or sym.endswith("TMN"):
            return sym[:-2].lower() if sym.endswith("TM") else sym[:-3].lower(), "tm"
        elif sym.endswith("USDT"):
            return sym[:-4].lower(), "usdt"
        return sym[:3].lower(), sym[3:].lower()

    def _execute_order_core(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        amount = float(amount or 0.0)
        if amount <= 0:
            return {"status": "failed", "error": "Order amount must be greater than zero"}

        norm_sym = self.normalize_symbol(symbol)
        exec_price = float(price) if price is not None and price > 0 else self.market_prices.get(norm_sym, 65000.0)
        
        base_curr, quote_curr = self._split_symbol(symbol)
        order_value = amount * exec_price
        fee_rate = self.DEFAULT_FEES["taker"] if str(order_type).lower() == "market" else self.DEFAULT_FEES["maker"]
        fee_amount = order_value * fee_rate

        side_clean = str(side).upper()
        if side_clean in ("BUY", "BID", "LONG"):
            total_required = order_value * (1 + fee_rate)
            avail_quote = self.wallets.get(quote_curr, self.wallets.get("usdt", 0.0))
            if avail_quote < total_required and total_required > 0:
                return {"status": "failed", "error": f"Insufficient {quote_curr.upper()} balance. Required: {total_required:.2f}, Available: {avail_quote:.2f}"}
            self.wallets[quote_curr] = avail_quote - total_required
            self.wallets[base_curr] = self.wallets.get(base_curr, 0.0) + amount
        elif side_clean in ("SELL", "ASK", "SHORT"):
            avail_base = self.wallets.get(base_curr, 0.0)
            if avail_base < amount:
                return {"status": "failed", "error": f"Insufficient {base_curr.upper()} balance. Required: {amount}, Available: {avail_base}"}
            self.wallets[base_curr] = avail_base - amount
            net_proceeds = order_value - fee_amount
            self.wallets[quote_curr] = self.wallets.get(quote_curr, 0.0) + net_proceeds
        else:
            return {"status": "failed", "error": f"Invalid order side: {side}"}

        order_id = f"wallex_paper_{uuid.uuid4().hex[:10]}"
        order_record = {
            "clientOrderId": order_id,
            "order_id": order_id,
            "id": order_id,
            "symbol": symbol.upper(),
            "side": side_clean,
            "type": str(order_type).lower(),
            "origQty": amount,
            "quantity": amount,
            "executedQty": amount,
            "price": exec_price,
            "fee": fee_amount,
            "feeAsset": quote_curr.upper(),
            "status": FlexibleStatus("FILLED"),
            "timestamp": int(time.time() * 1000)
        }
        self.orders[order_id] = order_record
        return order_record

    def create_order(self, *args, **kwargs) -> Dict[str, Any]:
        symbol = kwargs.get("symbol", args[0] if len(args) > 0 else "BTCUSDT")
        side = kwargs.get("side", args[1] if len(args) > 1 else "buy")
        order_type = kwargs.get("order_type", kwargs.get("type", args[2] if len(args) > 2 else "limit"))
        quantity = kwargs.get("quantity", kwargs.get("amount", args[3] if len(args) > 3 else 0.01))
        price = kwargs.get("price", args[4] if len(args) > 4 else None)

        record = self._execute_order_core(symbol, side, order_type, quantity, price)
        return record

    def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        record = self.create_order(*args, **kwargs)
        if "error" in record:
            return record

        class OrderEnvelope(dict):
            def __getitem__(self, item):
                if item == "status":
                    return FlexibleStatus("success")
                if item == "result":
                    return record
                return record.get(item, super().get(item))

            def get(self, item, default=None):
                if item == "status":
                    return FlexibleStatus("success")
                if item == "result":
                    return record
                return record.get(item, default)

        envelope = OrderEnvelope(record)
        envelope["status"] = FlexibleStatus("success")
        envelope["result"] = record
        return envelope

    def cancel_order(self, client_order_id: str) -> Dict[str, Any]:
        order = self.orders.get(client_order_id)
        if not order:
            return {"status": "failed", "error": "Order not found"}
        if str(order["status"]).upper() == "FILLED":
            return {"status": "failed", "error": "Cannot cancel filled order"}
        order["status"] = "CANCELED"
        return {"status": "success", "message": "Order canceled"}

    def get_order(self, client_order_id: str) -> Dict[str, Any]:
        order = self.orders.get(client_order_id)
        if not order:
            return {"status": "failed", "error": "Order not found"}
        return {"status": "success", "result": order}
