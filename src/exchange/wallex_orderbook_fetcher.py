import time
import requests
import logging

class WallexOrderbookFetcher:
    def __init__(self, base_url: str = "https://api.wallex.ir", max_retries: int = 3, timeout_sec: float = 4.0):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec
        self.logger = logging.getLogger("WallexOrderbookFetcher")
        self.consecutive_failures = 0
        self.max_allowed_consecutive_failures = 5

    def is_circuit_open(self) -> bool:
        return self.consecutive_failures >= self.max_allowed_consecutive_failures

    def fetch_orderbook(self, symbol: str) -> dict:
        if self.is_circuit_open():
            self.logger.warning(f"Circuit breaker OPEN. Skipping fetch for {symbol}.")
            return {"success": False, "reason": "CIRCUIT_BREAKER_OPEN"}

        url = f"{self.base_url}/v1/depth?symbol={symbol}"
        backoff = 0.5

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, timeout=self.timeout_sec)
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    bids = result.get("bid", [])
                    asks = result.get("ask", [])

                    if not bids or not asks:
                        return {"success": False, "reason": "EMPTY_ORDERBOOK"}

                    best_bid = float(bids[0].get("price", 0.0))
                    best_ask = float(asks[0].get("price", 0.0))

                    self.consecutive_failures = 0
                    return {
                        "success": True,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "bids_count": len(bids),
                        "asks_count": len(asks),
                        "reason": "OK"
                    }
                else:
                    self.logger.warning(f"Attempt {attempt}: Bad HTTP status {resp.status_code}")
            except Exception as e:
                self.logger.warning(f"Attempt {attempt} failed: {str(e)}")

            if attempt < self.max_retries:
                time.sleep(backoff)
                backoff *= 2.0

        self.consecutive_failures += 1
        return {"success": False, "reason": "FETCH_FAILED_TIMEOUT_OR_NETWORK"}
