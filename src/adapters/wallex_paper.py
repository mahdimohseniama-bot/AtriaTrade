import time
import requests
from typing import Dict, Any, List, Optional

class WallexPaperAdapter:
    def __init__(self, api_key: str = "paper_key", secret: str = "paper_secret", base_url: str = "https://api.wallex.ir"):
        self.api_key = api_key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.balance: Dict[str, float] = {"USDT": 1000.0, "BTC": 0.05, "TMN": 50000000.0}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.order_counter = 1000

    def get_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, float]:
        url = f"{self.base_url}/v1/markets"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                symbols_data = data.get("result", {}).get("symbols", {})
                
                # Check symbol variations (e.g., BTCUSDT, btcusdt)
                target = symbols_data.get(symbol) or symbols_data.get(symbol.upper()) or symbols_data.get(symbol.lower())
                if target:
                    stats = target.get("stats", {})
                    last_price = float(stats.get("lastPrice", target.get("lastPrice", 0.0)))
                    bid_price = float(stats.get("bidPrice", target.get("bidPrice", last_price)))
                    ask_price = float(stats.get("askPrice", target.get("askPrice", last_price)))
                    if last_price > 0:
                        return {"last": last_price, "bid": bid_price, "ask": ask_price}
        except Exception:
            pass

        # Fallback to last candle close price or reasonable synthetic default if API fails
        candles = self.get_candles(symbol, resolution="1", limit=1)
        if candles and len(candles) > 0:
            last_close = float(candles[-1].get("close", 65000.0))
            return {"last": last_close, "bid": last_close * 0.999, "ask": last_close * 1.001}

        return {"last": 65000.0, "bid": 64950.0, "ask": 65050.0}

    def get_candles(self, symbol: str = "BTCUSDT", resolution: str = "60", limit: int = 50) -> List[Dict[str, Any]]:
        # Resolution mapping for Wallex UDF (e.g. 60, 1D)
        url = f"{self.base_url}/v1/udf/history"
        now = int(time.time())
        # approximate 60s per bar unit
        step_seconds = int(resolution) * 60 if resolution.isdigit() else 3600
        from_ts = now - (step_seconds * limit)

        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_ts,
            "to": now
        }
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("s") == "ok":
                    t = data.get("t", [])
                    o = data.get("o", [])
                    h = data.get("h", [])
                    l = data.get("l", [])
                    c = data.get("c", [])
                    v = data.get("v", [])
                    candles = []
                    for i in range(len(t)):
                        candles.append({
                            "timestamp": t[i],
                            "open": float(o[i]),
                            "high": float(h[i]),
                            "low": float(l[i]),
                            "close": float(c[i]),
                            "volume": float(v[i])
                        })
                    if len(candles) > 0:
                        return candles
        except Exception:
            pass

        # Robust mock generator if offline or restricted
        mock_candles = []
        base_price = 65000.0
        for i in range(limit):
            t_stamp = now - ((limit - i) * step_seconds)
            p = base_price + (i * 10.0)
            mock_candles.append({
                "timestamp": t_stamp,
                "open": p - 5.0,
                "high": p + 15.0,
                "low": p - 10.0,
                "close": p,
                "volume": 1.5
            })
        return mock_candles

    def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        self.order_counter += 1
        order_id = f"wallex_paper_{self.order_counter}"
        
        exec_price = price if price and price > 0 else self.get_ticker(symbol)["last"]
        
        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side.lower(),
            "type": order_type.lower(),
            "quantity": quantity,
            "price": exec_price,
            "status": "filled",
            "timestamp": int(time.time())
        }
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders.get(order_id)
