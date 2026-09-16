import secrets
import time
from typing import Dict, Optional, Tuple


class SecureAuthManager:
    """
    مدیریت توکن‌های امن، کنترل دسترسی، تاریخ انقضا و جلوگیری از حملات Brute-force
    """
    def __init__(self, token_ttl_hours: float = 24.0, max_failed_attempts: int = 5, lockout_minutes: float = 15.0):
        self.token_ttl_seconds = token_ttl_hours * 3600.0
        self.max_failed_attempts = max_failed_attempts
        self.lockout_seconds = lockout_minutes * 60.0
        
        # ذخیره توکن‌ها: {token: {"username": ..., "role": ..., "created_at": ...}}
        self._tokens: Dict[str, dict] = {}
        # ثبت تلاش‌های ناموفق: {ip: {"count": ..., "last_failed": ..., "locked_until": ...}}
        self._failed_attempts: Dict[str, dict] = {}

    def generate_token_for_user(self, username: str, role: str = "read_only") -> str:
        """تولید یک توکن تصادفی با آنتروپی بالا و ثبت آن"""
        token = secrets.token_urlsafe(32)
        self._tokens[token] = {
            "username": username,
            "role": role,
            "created_at": time.time()
        }
        return token

    def generate_token(self, username: str, role: str = "read_only") -> str:
        """متد کمکی/مستعار برای تولید توکن"""
        return self.generate_token_for_user(username, role)

    def is_locked_out(self, client_ip: Optional[str]) -> bool:
        """بررسی قفل بودن آی‌پی به دلیل تلاش‌های ناموفق مکرر"""
        if not client_ip or client_ip not in self._failed_attempts:
            return False
        
        record = self._failed_attempts[client_ip]
        if time.time() < record.get("locked_until", 0):
            return True
        return False

    def record_failed_attempt(self, client_ip: Optional[str]):
        """ثبت تلاش ناموفق لاگین و قفل کردن IP در صورت عبور از سقف مجاز"""
        if not client_ip:
            return
        
        now = time.time()
        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = {"count": 1, "last_failed": now, "locked_until": 0}
        else:
            record = self._failed_attempts[client_ip]
            if now > record.get("locked_until", 0) and (now - record.get("last_failed", 0)) > self.lockout_seconds:
                record["count"] = 1
            else:
                record["count"] += 1
            
            record["last_failed"] = now
            if record["count"] >= self.max_failed_attempts:
                record["locked_until"] = now + self.lockout_seconds

    def authenticate_token(self, token: str, client_ip: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        اعتبارسنجی توکن بر اساس مقایسه مقاوم به حمله زمانی (Constant Time)، بررسی انقضا و وضعیت IP
        """
        if client_ip and self.is_locked_out(client_ip):
            return False, None, None

        matched_token_data = None
        for active_token, data in list(self._tokens.items()):
            if secrets.compare_digest(active_token, token):
                matched_token_data = data
                break

        if not matched_token_data:
            if client_ip:
                self.record_failed_attempt(client_ip)
            return False, None, None

        # بررسی انقضا
        if (time.time() - matched_token_data["created_at"]) > self.token_ttl_seconds:
            return False, None, None

        # پاک کردن تلاش ناموفق در صورت لاگین موفق
        if client_ip and client_ip in self._failed_attempts:
            del self._failed_attempts[client_ip]

        return True, matched_token_data["username"], matched_token_data["role"]

    def authenticate(self, token: str, client_ip: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """متد مستعار جهت سازگاری کامل با DashboardServer"""
        return self.authenticate_token(token, client_ip)

    def revoke_token(self, token: str) -> bool:
        """ابطال صریح توکن"""
        for active_token in list(self._tokens.keys()):
            if secrets.compare_digest(active_token, token):
                del self._tokens[active_token]
                return True
        return False
