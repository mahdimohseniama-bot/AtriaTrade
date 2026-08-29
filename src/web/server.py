import json
from fastapi import FastAPI, HTTPException, Header, Query
from typing import Any, Optional

class DashboardStateProvider:
    def __init__(self):
        self._status = "ACTIVE"
        self.positions = {"open_positions": [], "open_positions_count": 0}
        self.state = {"paused": False}
        self.panic_triggered = False
        self.connected_clients = []

    def get_status(self) -> str:
        return self._status

    def pause_trading(self) -> str:
        self._status = "PAUSED"
        self.state["paused"] = "paused"
        return self._status

    def resume_trading(self) -> str:
        # Check for panic state
        if self.state.get("panic"):
            raise ValueError("Cannot resume while Panic")
            
        self._status = "ACTIVE"
        self.state["paused"] = False
        self.state.pop("panic", None) 
        return self._status

    @property
    def is_paused(self):
        return self.state.get("paused") == "paused"

    def trigger_panic(self):
        self.panic_triggered = True
        self.state["panic"] = True
        self.state["paused"] = "paused"
        self._status = "PANIC_LOCKED"

    def set_custom_state(self, key: str, value: Any):
        self.positions[key] = value

    def connect_client(self, client):
        self.connected_clients.append(client)

    def disconnect_client(self, client):
        if client in self.connected_clients:
            self.connected_clients.remove(client)

    async def broadcast_state(self, data: dict):
        for client in self.connected_clients:
            client.sent_messages.append(json.dumps(data))

class WebApiRouter:
    def __init__(self, provider: Any):
        self.provider = provider

    def handle_get_status(self) -> dict:
        return {
            "status": self.provider.get_status(),
            "total_balance_usdt": self.provider.positions.get("total_balance_usdt", 0),
            "positions": self.provider.positions.get("open_positions", []),
            "open_positions_count": self.provider.positions.get("open_positions_count", 0)
        }

    def handle_get_positions(self) -> dict:
        positions = self.provider.positions.get("open_positions", [])
        return {"count": len(positions), "positions": positions}

    def handle_pause(self) -> dict:
        self.provider.pause_trading()
        return {"status": "success", "state": "paused"}

    def handle_resume(self) -> dict:
        self.provider.resume_trading()
        return {"status": "success", "state": "running"}

    def handle_panic(self, **kwargs) -> dict:
        self.provider.trigger_panic()
        return {"status": "emergency_locked", "action": "panic_triggered"}

    async def handle_ws_message(self, client, message: str) -> str:
        if message == "ping":
            return json.dumps({"type": "pong"})
        return json.dumps({"type": "unknown"})

class WebServer:
    def __init__(self, api_token: Optional[str] = None):
        self.app = FastAPI()
        self.api_token = api_token
        self.provider = DashboardStateProvider()
        self.router_logic = WebApiRouter(self.provider)
        
        @self.app.get("/api/status")
        async def api_status():
            return self.router_logic.handle_get_status()

        @self.app.post("/api/pause")
        async def api_pause(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
            self._check_auth(authorization, token)
            return self.router_logic.handle_pause()

        @self.app.post("/api/resume")
        async def api_resume(x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
            header_token = x_api_key or authorization
            self._check_auth(header_token, token)
            return self.router_logic.handle_resume()

        @self.app.post("/api/panic")
        async def api_panic(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
            self._check_auth(authorization, token)
            return self.router_logic.handle_panic()

    def _check_auth(self, auth_header: Optional[str], query_token: Optional[str] = None):
        token_to_check = None
        if auth_header:
            token_to_check = auth_header.replace("Bearer ", "")
        elif query_token:
            token_to_check = query_token
            
        if token_to_check != self.api_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

web_server = WebServer(api_token="test-token")
app = web_server.app
