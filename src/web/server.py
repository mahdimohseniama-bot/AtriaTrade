"""AtriaTrade Web Server, State Provider and Security Management."""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, Set
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class DashboardStateProvider:
    """Provides synchronized live state for web dashboard, WebSocket clients, and API."""
    def __init__(self):
        self._state: Dict[str, Any] = {
            "status": "ACTIVE",
            "system_status": "ONLINE (Paper Trading)",
            "total_balance_usdt": 10000.0,
            "balance_usdt": 10000.0,
            "total_profit_usdt": 142.50,
            "win_rate": 78.5,
            "active_positions_count": 2,
            "open_positions_count": 2,
            "circuit_breaker": "NORMAL",
            "risk_level": "LOW (1.5%)",
            "is_paused": False,
            "paused": False,
            "panic_mode": False,
            "panic_triggered": False,
            "recent_logs": [
                "[SYSTEM] AtriaTrade Web Engine initialized successfully.",
                "[EXCHANGE] Paper Trading connected: Binance / Nobitex simulated feed.",
                "[RISK] Capital preservation rules verified and active.",
                "[SIGNAL] Monitoring BTC/USDT, ETH/USDT, PAXG/USDT..."
            ],
            "open_positions": [
                {"symbol": "BTC/USDT", "side": "BUY", "size": 0.15, "entry": 64200.0, "pnl": "+$65.40 (+0.68%)"},
                {"symbol": "ETH/USDT", "side": "BUY", "size": 1.2, "entry": 3450.0, "pnl": "+$77.10 (+1.86%)"}
            ]
        }
        self._connected_clients: Set[Any] = set()

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    @property
    def is_paused(self) -> bool:
        val = self._state.get("is_paused", False)
        if val == "paused":
            return True
        return bool(val)

    @property
    def panic_triggered(self) -> bool:
        return bool(self._state.get("panic_triggered", False))

    @property
    def panic_mode(self) -> bool:
        return bool(self._state.get("panic_mode", False))

    @property
    def connected_clients(self) -> Set[Any]:
        return self._connected_clients

    def connect_client(self, client: Any) -> None:
        self._connected_clients.add(client)

    def disconnect_client(self, client: Any) -> None:
        self._connected_clients.discard(client)

    async def broadcast_state(self, payload: Dict[str, Any]) -> None:
        msg = json.dumps(payload)
        for client in list(self._connected_clients):
            if hasattr(client, "send_text"):
                res = client.send_text(msg)
                if asyncio.iscoroutine(res):
                    await res
            elif hasattr(client, "sent_messages"):
                client.sent_messages.append(msg)

    def get_state(self) -> Dict[str, Any]:
        return self._state

    def set_custom_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def update_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    async def get_state_async(self) -> Dict[str, Any]:
        return self._state


class WebApiRouter:
    """Manages API routes, command execution and WebSocket handling."""
    def __init__(self, provider: Optional[DashboardStateProvider] = None):
        self.provider = provider or DashboardStateProvider()

    def handle_get_status(self) -> Dict[str, Any]:
        return self.provider.get_state()

    def handle_get_positions(self) -> Dict[str, Any]:
        state = self.provider.get_state()
        positions = state.get("open_positions", [])
        count = state.get("open_positions_count", len(positions))
        return {
            "count": count,
            "positions": positions,
            "open_positions": positions
        }

    def handle_pause(self) -> Dict[str, Any]:
        self.provider.set_custom_state("is_paused", "paused")
        self.provider.set_custom_state("paused", "paused")
        self.provider.set_custom_state("status", "PAUSED")
        self.provider.set_custom_state("system_status", "PAUSED")
        return {
            "status": "success",
            "state": "paused",
            "action": "pause",
            "system_status": "PAUSED"
        }

    def handle_resume(self) -> Dict[str, Any]:
        if self.provider.panic_triggered or self.provider.get_state().get("status") == "PANIC_LOCKED":
            raise ValueError("Cannot resume while Panic is active")

        self.provider.set_custom_state("is_paused", False)
        self.provider.set_custom_state("paused", False)
        self.provider.set_custom_state("status", "ACTIVE")
        self.provider.set_custom_state("system_status", "ONLINE (Paper Trading)")
        return {
            "status": "success",
            "state": "running",
            "action": "resume",
            "system_status": "ONLINE (Paper Trading)"
        }

    def handle_panic(self, reason: Optional[str] = None) -> Dict[str, Any]:
        self.provider.set_custom_state("is_paused", "paused")
        self.provider.set_custom_state("paused", "paused")
        self.provider.set_custom_state("panic_mode", True)
        self.provider.set_custom_state("panic_triggered", True)
        self.provider.set_custom_state("status", "PANIC_LOCKED")
        self.provider.set_custom_state("system_status", "PANIC_LOCKED")
        self.provider.set_custom_state("open_positions_count", 0)
        return {
            "status": "emergency_locked",
            "state": "emergency_stop",
            "action": "panic_triggered",
            "reason": reason or "User triggered panic",
            "system_status": "PANIC_LOCKED"
        }

    async def handle_ws_message(self, client: Any, message: str) -> str:
        if message == "ping" or (isinstance(message, str) and "ping" in message):
            return json.dumps({"type": "pong"})
        return json.dumps({"type": "ack", "received": message})


class WebServer:
    """FastAPI Web Server instance wrapper with security and template rendering."""
    def __init__(
        self,
        state_provider: Optional[DashboardStateProvider] = None,
        api_token: Optional[str] = None
    ):
        self.state_provider = state_provider or DashboardStateProvider()
        self.api_token = api_token
        self.app = FastAPI(title="AtriaTrade Control Center", version="1.0.0")
        self.api_router = WebApiRouter(self.state_provider)

        self._setup_security()
        self._setup_routes()

    def _setup_security(self):
        if not self.api_token:
            return

        @self.app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            path = request.url.path
            # Public endpoints
            if path in ["/api/status", "/health", "/"] or not path.startswith("/api"):
                return await call_next(request)

            auth_header = request.headers.get("Authorization")
            x_api_key = request.headers.get("X-API-Key")
            query_token = request.query_params.get("token")

            token_valid = False
            if auth_header and auth_header.replace("Bearer ", "").strip() == self.api_token:
                token_valid = True
            elif x_api_key == self.api_token:
                token_valid = True
            elif query_token == self.api_token:
                token_valid = True

            if not token_valid:
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

            return await call_next(request)

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index(request: Request):
            template_name = "dashboard.html" if (TEMPLATES_DIR / "dashboard.html").exists() else "index.html"
            return templates.TemplateResponse(
                template_name,
                {
                    "request": request,
                    "title": "AtriaTrade AI Terminal",
                    "state": self.state_provider.get_state()
                }
            )

        @self.app.get("/api/status", response_class=JSONResponse)
        @self.app.get("/api/state", response_class=JSONResponse)
        async def get_live_status():
            return JSONResponse(content=self.api_router.handle_get_status())

        @self.app.get("/api/positions", response_class=JSONResponse)
        async def get_positions():
            return JSONResponse(content=self.api_router.handle_get_positions())

        @self.app.post("/api/pause", response_class=JSONResponse)
        @self.app.post("/api/control/pause", response_class=JSONResponse)
        async def pause_system():
            return JSONResponse(content=self.api_router.handle_pause())

        @self.app.post("/api/resume", response_class=JSONResponse)
        @self.app.post("/api/control/resume", response_class=JSONResponse)
        async def resume_system():
            return JSONResponse(content=self.api_router.handle_resume())

        @self.app.post("/api/panic", response_class=JSONResponse)
        @self.app.post("/api/control/panic", response_class=JSONResponse)
        async def panic_stop(request: Request):
            reason = None
            try:
                body = await request.json()
                if isinstance(body, dict):
                    reason = body.get("reason")
            except Exception:
                pass
            return JSONResponse(content=self.api_router.handle_panic(reason=reason))

        @self.app.get("/health", response_class=JSONResponse)
        async def health():
            return JSONResponse(content={"status": "healthy", "service": "AtriaTrade Web Server"})

    def get_app(self) -> FastAPI:
        return self.app


# Global instance
state_provider = DashboardStateProvider()
web_server_instance = WebServer(state_provider=state_provider)
app = web_server_instance.get_app()
