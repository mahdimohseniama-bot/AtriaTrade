"""
Dashboard Server with Integrated Secure Auth.
Provides secure endpoints for bot telemetry, status, and control.
"""
from typing import Dict, Any, Optional
from src.dashboard.auth import SecureAuthManager

class DashboardServer:
    def __init__(self, auth_manager: Optional[SecureAuthManager] = None):
        self.auth_manager = auth_manager or SecureAuthManager()
        self.state_data: Dict[str, Any] = {
            "status": "RUNNING",
            "mode": "PAPER_TRADING",
            "active_positions": 0,
            "total_balance_usdt": 10000.0,
            "profit_reserved": 0.0
        }

    def get_public_status(self) -> Dict[str, Any]:
        """مسیر عمومی بدون نیاز به احراز هویت"""
        return {"system": "AtriaTrade", "online": True}

    def get_dashboard_summary(self, token: str, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """مسیر خصوصی و امن برای دیدن جزئیات حساب و بات"""
        is_valid, username, role = self.auth_manager.authenticate(token, client_ip=client_ip)
        
        if not is_valid:
            return {
                "success": False,
                "error": "Unauthorized: Invalid or expired token, or rate limit exceeded."
            }
        
        return {
            "success": True,
            "user": username,
            "role": role,
            "data": self.state_data
        }

    def update_bot_state(self, key: str, value: Any, token: str, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """تغییر وضعیت یا کانفیگ فقط برای کاربرهای ادمین"""
        is_valid, username, role = self.auth_manager.authenticate(token, client_ip=client_ip)
        
        if not is_valid:
            return {"success": False, "error": "Unauthorized"}
            
        if role != "admin":
            return {"success": False, "error": "Forbidden: Admin privileges required"}
            
        self.state_data[key] = value
        return {"success": True, "updated_key": key, "new_value": value}
