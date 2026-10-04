import requests
import logging
import hmac
import hashlib
import time

class WallexAccountFetcher:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.wallex.ir"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger("WallexAccountFetcher")

    def _get_headers(self) -> dict:
        timestamp = str(int(time.time() * 1000))
        # Simple signature placeholder for the logic structure
        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    def fetch_balance(self, asset: str) -> dict:
        # Mocking the call structure for now since actual secret key handling 
        # should be injected via environment variables later.
        if not self.api_key or self.api_key == "MOCK_KEY":
            return {"success": True, "balance": 1000.0, "asset": asset, "note": "MOCK_MODE"}
            
        url = f"{self.base_url}/v1/account/balances"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                balances = data.get("result", {}).get("balances", {})
                return {"success": True, "balance": float(balances.get(asset, 0.0))}
            return {"success": False, "reason": f"HTTP_{resp.status_code}"}
        except Exception as e:
            self.logger.error(f"Account fetch failed: {e}")
            return {"success": False, "reason": "CONNECTION_ERROR"}
