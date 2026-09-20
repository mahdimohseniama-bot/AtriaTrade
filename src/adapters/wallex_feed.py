import requests
import time
from typing import List, Dict, Any, Optional

class WallexDataFeed:
    """
    دریافت کندل‌های زنده و دیتای مارکت از والکس (Public API)
    """
    BASE_URL = "https://api.wallex.ir/v1"

    def __init__(self, symbol: str = "BTCUSDT", resolution: str = "60", timeout: int = 10):
        # تبدیل نماد به فرمت استاندارد والکس (مثلا BTC/USDT -> BTCUSDT)
        self.symbol = symbol.replace("/", "").replace("-", "").replace("_", "").upper()
        self.resolution = resolution  # 1, 5, 15, 60, 240, 1D
        self.timeout = timeout

    def get_ohlcv(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        دریافت کندل‌های تاریخی و زنده برای گرم‌کردن فیلتر رژیم و SMC
        """
        now = int(time.time())
        # محاسبه بازه زمانی بر اساس رزولوشن
        resolution_seconds = int(self.resolution) * 60 if self.resolution.isdigit() else 3600
        from_time = now - (limit * resolution_seconds * 2)

        url = f"{self.BASE_URL}/udf/history"
        params = {
            "symbol": self.symbol,
            "resolution": self.resolution,
            "from": from_time,
            "to": now
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            if response.status_code != 200:
                return []
            
            data = response.json()
            if data.get("s") != "ok" or not data.get("t"):
                return []

            candles = []
            timestamps = data["t"]
            opens = data["o"]
            highs = data["h"]
            lows = data["l"]
            closes = data["c"]
            volumes = data.get("v", [0] * len(timestamps))

            for i in range(len(timestamps)):
                candles.append({
                    "timestamp": timestamps[i] * 1000 if timestamps[i] < 1e11 else timestamps[i],
                    "open": float(opens[i]),
                    "high": float(highs[i]),
                    "low": float(lows[i]),
                    "close": float(closes[i]),
                    "volume": float(volumes[i])
                })

            # بازگرداندن به تعداد limit خواسته شده
            return candles[-limit:]

        except Exception as e:
            # مدیریت خطای اتصال یا قطعی موقت
            return []

    def get_latest_price(self) -> Optional[float]:
        """
        دریافت آخرین قیمت لحظه‌ای برای سینک کردن آداپتور
        """
        url = f"{self.BASE_URL}/markets"
        try:
            res = requests.get(url, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                symbols_data = data.get("result", {}).get("symbols", {})
                if self.symbol in symbols_data:
                    return float(symbols_data[self.symbol]["stats"]["lastPrice"])
        except Exception:
            pass
        return None
