import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LiveGuardConfig:
    allow_live: bool
    kill_switch: bool
    api_key_present: bool
    api_secret_present: bool

class WallexLiveGuard:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""

    def read_config(self) -> LiveGuardConfig:
        allow_live_env = os.environ.get("ALLOW_WALLEX_LIVE", "").strip().lower()
        kill_switch_env = os.environ.get("WALLEX_KILL_SWITCH", "").strip().lower()

        api_key = self.api_key or os.environ.get("WALLEX_API_KEY", "")
        api_secret = self.api_secret or os.environ.get("WALLEX_API_SECRET", "")

        return LiveGuardConfig(
            allow_live=allow_live_env in ("1", "true", "yes", "on"),
            kill_switch=kill_switch_env in ("1", "true", "yes", "on"),
            api_key_present=bool(str(api_key).strip()),
            api_secret_present=bool(str(api_secret).strip())
        )

    def can_execute_safely(self) -> bool:
        cfg = self.read_config()
        return (
            cfg.allow_live
            and not cfg.kill_switch
            and cfg.api_key_present
            and cfg.api_secret_present
        )

    def verify_order_placement(self, dry_run: bool = False) -> None:
        if dry_run:
            return

        cfg = self.read_config()

        if cfg.kill_switch:
            raise RuntimeError("LIVE_BLOCKED: Kill switch is actively engaged.")
        if not cfg.allow_live:
            raise RuntimeError("LIVE_BLOCKED: ALLOW_WALLEX_LIVE is not enabled.")
        if not (cfg.api_key_present and cfg.api_secret_present):
            raise RuntimeError("LIVE_BLOCKED: Wallex API credentials are missing.")
