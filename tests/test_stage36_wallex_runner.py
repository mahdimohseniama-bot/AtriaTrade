import pytest
from unittest.mock import MagicMock
from src.core.wallex_live_runner import WallexLiveRunner, WallexRunnerConfig

class DummyWallexClient:
    def ping(self):
        return True

    def get_open_orders(self, symbol="BTCUSDT"):
        return []

    def get_balances(self):
        return {"USDT": 100.0, "BTC": 0.005}

    def place_order(self, symbol, side, order_type, quantity, price=None):
        return {"id": "W-LIVE-1001", "status": "FILLED", "price": price, "quantity": quantity}

def test_stage36_runner_init_and_default_config():
    client = DummyWallexClient()
    runner = WallexLiveRunner(exchange_client=client)
    
    assert runner.config.dry_run is True
    assert runner.config.symbol == "BTCUSDT"
    assert runner.orchestrator is not None
    assert runner.heartbeat.client == client

def test_stage36_runner_single_tick_healthy():
    client = DummyWallexClient()
    cfg = WallexRunnerConfig(symbol="ETHUSDT", dry_run=True)
    runner = WallexLiveRunner(config=cfg, exchange_client=client)

    result = runner.run_single_tick(sample_signal=None)
    assert runner.iteration_count == 1
    assert result.network_healthy is True
    assert result.latency_ms >= 0.0
    assert result.status == "SKIPPED_NO_SIGNAL"

def test_stage36_runner_bounded_loop_execution():
    client = DummyWallexClient()
    cfg = WallexRunnerConfig(poll_interval_sec=0.01, dry_run=True)
    runner = WallexLiveRunner(config=cfg, exchange_client=client)

    runner.start_monitoring_loop(max_ticks=3)
    assert runner.iteration_count == 3
    assert runner.running is True
