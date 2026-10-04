import os
import requests
from typing import Dict, Any, Optional
from src.exchange.wallex_micro_plan import MicroOrderPlan
from src.exchange.wallex_live_guard import WallexLiveGuard

class WallexLiveExecutor:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.environ.get("WALLEX_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("WALLEX_API_SECRET", "")
        self.session = requests.Session()
        self.guard = WallexLiveGuard(api_key=self.api_key, api_secret=self.api_secret)

    def execute_plan(self, plan: MicroOrderPlan) -> Dict[str, Any]:
        if not plan.is_valid:
            return {
                "status": "REJECTED",
                "reason": plan.rejection_reason or "INVALID_PLAN"
            }

        allow_live = os.environ.get("ALLOW_WALLEX_LIVE", "0") == "1"
        kill_switch = os.environ.get("WALLEX_KILL_SWITCH", "0") == "1"

        if not allow_live or kill_switch:
            return {
                "status": "DRY_RUN_SUCCESS",
                "order_id": "sim_wallex_1001",
                "symbol": plan.symbol,
                "side": plan.side,
                "price": plan.target_price,
                "quantity": plan.quantity
            }

        payload = {
            "symbol": plan.symbol,
            "type": "LIMIT",
            "side": plan.side,
            "price": plan.target_price,
            "quantity": plan.quantity
        }
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        resp = self.session.post("https://api.wallex.ir/v1/orders", json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            order_id = data.get("result", {}).get("id", "live_unknown")
            return {
                "status": "LIVE_PLACED",
                "order_id": order_id,
                "symbol": plan.symbol,
                "side": plan.side,
                "price": plan.target_price,
                "quantity": plan.quantity
            }

        return {
            "status": "REJECTED",
            "reason": f"API_ERROR_{resp.status_code}"
        }
