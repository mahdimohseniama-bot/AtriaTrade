"""
Unit tests for Web Dashboard Server, State Provider & Router.
Pure standard Python asyncio execution without external pytest plugins.
"""

import pytest
import asyncio
import json
from src.web.server import DashboardStateProvider, WebApiRouter


class MockWebSocketClient:
    def __init__(self):
        self.sent_messages = []

    async def send_text(self, text: str):
        self.sent_messages.append(text)


def test_api_status_and_positions():
    provider = DashboardStateProvider()
    provider.set_custom_state("total_balance_usdt", 12500.0)
    provider.set_custom_state("open_positions", [{"symbol": "BTC/USDT", "side": "BUY", "size": 0.1}])
    provider.set_custom_state("open_positions_count", 1)

    router = WebApiRouter(provider)

    # 1. Test Status
    status = router.handle_get_status()
    assert status["status"] == "ACTIVE"
    assert status["total_balance_usdt"] == 12500.0
    assert status["open_positions_count"] == 1

    # 2. Test Positions
    pos_data = router.handle_get_positions()
    assert pos_data["count"] == 1
    assert pos_data["positions"][0]["symbol"] == "BTC/USDT"


def test_control_pause_resume_panic():
    provider = DashboardStateProvider()
    router = WebApiRouter(provider)

    # 1. Pause
    pause_res = router.handle_pause()
    assert pause_res["status"] == "success"
    assert provider.is_paused is True
    assert router.handle_get_status()["status"] == "PAUSED"

    # 2. Resume
    resume_res = router.handle_resume()
    assert resume_res["status"] == "success"
    assert provider.is_paused is False
    assert router.handle_get_status()["status"] == "ACTIVE"

    # 3. Panic
    panic_res = router.handle_panic(reason="High Volatility Spike")
    assert panic_res["status"] == "emergency_locked"
    assert provider.panic_triggered is True
    assert provider.is_paused is True
    assert router.handle_get_status()["status"] == "PANIC_LOCKED"

    # 4. Resume while panic is active must raise ValueError
    with pytest.raises(ValueError, match="Cannot resume while Panic"):
        router.handle_resume()


def test_websocket_broadcast_and_heartbeat():
    async def _async_suite():
        provider = DashboardStateProvider()
        router = WebApiRouter(provider)

        client1 = MockWebSocketClient()
        client2 = MockWebSocketClient()

        provider.connect_client(client1)
        provider.connect_client(client2)
        assert len(provider.connected_clients) == 2

        # Broadcast test
        await provider.broadcast_state({"type": "update", "val": 42})
        assert len(client1.sent_messages) == 1
        assert json.loads(client1.sent_messages[0]) == {"type": "update", "val": 42}
        assert len(client2.sent_messages) == 1

        # WebSocket Ping Pong
        pong = await router.handle_ws_message(client1, "ping")
        assert json.loads(pong) == {"type": "pong"}

        # Disconnect
        provider.disconnect_client(client1)
        assert len(provider.connected_clients) == 1

    asyncio.run(_async_suite())
