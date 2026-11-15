import requests
import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger("WallexPaperAdapter")

class WallexPaperAdapter:
    DEFAULT_FEES: Dict[str, float] = {
        "maker": 0.002,
        "taker": 0.002,
        "spread_barrier": 0.004
    }

    def __init__(
        self,
        base_url: str = "https://api.wallex.ir",
        default_symbol: str = "USDTTMN",
        timeout: int = 5,
        initial_balances: Optional[Dict[str, float]] = None,
        **kwargs
    ):
        self.base_url = base_url.rstrip('/')
        self.default_symbol = default_symbol
        self.timeout = timeout
        
        default_bals = {"TMN": 100_000_000.0, "TM": 100_000_000.0, "USDT": 1000.0, "BTC": 0.05}
        
        self.paper_balances: Dict[str, float] = {}
        if initial_balances is not None:
            for k, v in initial_balances.items():
                key_upper = k.upper()
                self.paper_balances[key_upper] = float(v)
                if key_upper == "TMN":
                    self.paper_balances["TM"] = float(v)
                elif key_upper == "TM":
                    self.paper_balances["TMN"] = float(v)
        else:
            self.paper_balances = default_bals.copy()

        self.initial_balances = self.paper_balances.copy()
        self.mock_prices: Dict[str, float] = {}
        self.orders: List[Dict[str, Any]] = []

    def normalize_symbol(self, symbol: Optional[str] = None) -> str:
        s = symbol or self.default_symbol
        return s.replace("_", "").upper()

    def set_market_price(self, symbol: str, price: float) -> None:
        p = float(price)
        self.mock_prices[symbol] = p
        self.mock_prices[self.normalize_symbol(symbol)] = p

    def get_market_price(self, symbol: Optional[str] = None) -> float:
        sym = symbol or self.default_symbol
        norm = self.normalize_symbol(sym)
        if sym in self.mock_prices:
            return self.mock_prices[sym]
        if norm in self.mock_prices:
            return self.mock_prices[norm]
        
        best = self.get_best_prices(norm)
        if best.get("ask") and best.get("bid"):
            return (best["ask"] + best["bid"]) / 2.0
        return 268000.0 if "TMN" in norm or "TM" in norm else 65000.0

    def get_orderbook(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        sym = symbol or self.default_symbol
        norm = self.normalize_symbol(sym)
        
        p = self.mock_prices.get(sym) or self.mock_prices.get(norm)
        if p is not None:
            return {
                "success": True,
                "bids": [{"price": p * 0.999, "quantity": 10.0}],
                "asks": [{"price": p * 1.001, "quantity": 10.0}]
            }

        url = f"{self.base_url}/v1/depth"
        params = {"symbol": norm}
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("result", {})
                raw_bids = result.get("bid", result.get("bids", []))
                raw_asks = result.get("ask", result.get("asks", []))

                bids = []
                for b in raw_bids:
                    price = float(b[0] if isinstance(b, list) else b.get("price", 0))
                    qty = float(b[1] if isinstance(b, list) else b.get("quantity", 0))
                    if price > 0:
                        bids.append({"price": price, "quantity": qty})

                asks = []
                for a in raw_asks:
                    price = float(a[0] if isinstance(a, list) else a.get("price", 0))
                    qty = float(a[1] if isinstance(a, list) else a.get("quantity", 0))
                    if price > 0:
                        asks.append({"price": price, "quantity": qty})

                if bids or asks:
                    return {"success": True, "bids": bids, "asks": asks}
        except Exception as e:
            logger.debug(f"Depth fetch error: {e}")

        base_p = 268000.0 if "TMN" in norm or "TM" in norm else 65000.0
        return {
            "success": True,
            "bids": [{"price": base_p * 0.9995, "quantity": 5.0}],
            "asks": [{"price": base_p * 1.0005, "quantity": 5.0}]
        }

    def get_best_prices(self, symbol: Optional[str] = None) -> Dict[str, Optional[float]]:
        ob = self.get_orderbook(symbol)
        best_bid = ob["bids"][0]["price"] if ob.get("bids") else None
        best_ask = ob["asks"][0]["price"] if ob.get("asks") else None
        return {"bid": best_bid, "ask": best_ask}

    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        sym = symbol or self.default_symbol
        norm = self.normalize_symbol(sym)
        last_price = self.get_market_price(sym)
        best = self.get_best_prices(norm)
        bid = best.get("bid") or last_price
        ask = best.get("ask") or last_price
        return {
            "symbol": norm,
            "last_price": last_price,
            "last": last_price,
            "price": last_price,
            "bid": bid,
            "ask": ask,
            "bidPrice": bid,
            "askPrice": ask,
            "volume_24h": 100000.0
        }

    def get_candles(self, symbol: Optional[str] = None, resolution: str = "15m", limit: int = 100) -> List[Dict[str, Any]]:
        curr = self.get_market_price(symbol)
        now = int(time.time())
        candles = []
        step = 900 if resolution == "15m" else (60 if resolution == "1m" else 3600)
        for i in range(limit):
            t = now - (limit - i) * step
            candles.append({
                "time": t,
                "timestamp": t,
                "open": curr,
                "high": curr * 1.001,
                "low": curr * 0.999,
                "close": curr,
                "volume": 10.0
            })
        return candles

    def get_balance(self, asset: str) -> float:
        return float(self.paper_balances.get(asset.upper(), 0.0))

    def get_balances(self) -> Dict[str, float]:
        return {k.lower(): v for k, v in self.paper_balances.items()}

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "market",
        quantity: float = 0.0,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        return self.execute_paper_order(side=side, symbol=symbol, quantity=quantity, price=price)

    def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        res = None
        # Support both 'quantity' and 'amount' keys for compatibility
        qty = kwargs.get("quantity") or kwargs.get("amount") or 0.0
        
        if "order_type" in kwargs or "side" in kwargs:
            res = self.create_order(
                symbol=kwargs.get("symbol", self.default_symbol),
                side=kwargs.get("side", "buy"),
                order_type=kwargs.get("order_type", "market"),
                quantity=float(qty),
                price=kwargs.get("price")
            )
        elif len(args) >= 3:
            res = self.create_order(
                symbol=args[0],
                side=args[1],
                order_type=args[2],
                quantity=float(args[3]) if len(args) > 3 else 0.0
            )
        else:
            return {"status": "rejected", "reason": "Invalid arguments"}
        
        # Build Wallex API envelope while keeping direct keys
        out = dict(res)
        out["status"] = "success"
        out["result"] = {
            "status": "FILLED",
            "side": res.get("side"),
            "symbol": res.get("symbol"),
            "price": res.get("price"),
            "quantity": res.get("quantity"),
            "total_cost": res.get("total_cost")
        }
        return out

    def execute_paper_order(
        self,
        side: str,
        symbol: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        side = side.lower()
        norm = self.normalize_symbol(symbol)
        exec_price = float(price) if price else self.get_market_price(symbol)

        quote_asset = "TMN" if "TMN" in norm else ("TM" if "TM" in norm else "USDT")
        base_asset = norm.replace(quote_asset, "") or "USDT"

        cost = quantity * exec_price
        if side == "buy":
            current_quote = self.get_balance(quote_asset)
            if current_quote < cost:
                return {"status": "rejected", "reason": f"Insufficient {quote_asset} balance"}
            self.paper_balances[quote_asset] = current_quote - cost
            if quote_asset == "TMN":
                self.paper_balances["TM"] = self.paper_balances[quote_asset]
            elif quote_asset == "TM":
                self.paper_balances["TMN"] = self.paper_balances[quote_asset]

            self.paper_balances[base_asset] = self.get_balance(base_asset) + quantity
        elif side == "sell":
            current_base = self.get_balance(base_asset)
            if current_base < quantity:
                return {"status": "rejected", "reason": f"Insufficient {base_asset} balance"}
            self.paper_balances[base_asset] = current_base - quantity
            new_quote_bal = self.get_balance(quote_asset) + cost
            self.paper_balances[quote_asset] = new_quote_bal
            if quote_asset == "TMN":
                self.paper_balances["TM"] = new_quote_bal
            elif quote_asset == "TM":
                self.paper_balances["TMN"] = new_quote_bal
        else:
            return {"status": "rejected", "reason": f"Unknown side: {side}"}

        record = {
            "status": "filled",
            "side": side,
            "symbol": norm,
            "price": exec_price,
            "executed_price": exec_price,
            "quantity": float(quantity),
            "total_cost": cost,
            "timestamp": time.time()
        }
        self.orders.append(record)
        return record
