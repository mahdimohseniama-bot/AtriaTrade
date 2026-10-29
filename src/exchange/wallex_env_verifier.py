import os
import re
from typing import Dict, Any

class WallexEnvVerifier:
    @staticmethod
    def verify() -> Dict[str, Any]:
        api_key = os.getenv("WALLEX_API_KEY", "").strip()
        live_mode = os.getenv("ATRIA_LIVE_MODE", "0").strip().lower() in ("1", "true", "yes")
        kill_switch = os.getenv("ATRIA_KILL_SWITCH", "0").strip().lower() in ("1", "true", "yes")
        symbol = os.getenv("WALLEX_SYMBOL", "TMNUSDT").strip().upper()
        
        has_valid_key = bool(api_key and len(api_key) >= 10)
        
        is_executable = (not kill_switch) and (not live_mode or has_valid_key)
        
        return {
            "api_key_configured": has_valid_key,
            "live_mode_enabled": live_mode,
            "kill_switch_active": kill_switch,
            "target_symbol": symbol,
            "execution_ready": is_executable,
            "mode_label": "LIVE" if (live_mode and not kill_switch and has_valid_key) else "DRY_RUN"
        }
