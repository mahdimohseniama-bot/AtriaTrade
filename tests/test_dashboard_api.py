import pytest
from src.dashboard.api import ReadOnlyDashboardAPI
from src.core.monitoring import SystemHealthMonitor, SystemAlertManager, AlertLevel

class MockPortfolioManager:
    def __init__(self):
        self.balance = 10000.0
        self.positions = {"BTCUSDT": {"amount": 0.5, "entry_price": 50000.0}}

    def get_portfolio_summary(self):
        return {
            "status": "HEALTHY",
            "total_equity": 10000.0,
            "open_positions": 1,
            "positions": self.positions
        }

def test_dashboard_api_initialization():
    api = ReadOnlyDashboardAPI()
    summary = api.get_system_summary()
    assert "health" in summary
    assert summary["health"]["status"] == "HEALTHY"
    assert summary["mode"] == "PAPER_TRADING_READ_ONLY"

def test_dashboard_api_with_alerts():
    alert_mgr = SystemAlertManager()
    alert_mgr.trigger_alert(AlertLevel.WARNING, "High Latency", "Network lag detected")
    monitor = SystemHealthMonitor(alert_manager=alert_mgr)
    
    api = ReadOnlyDashboardAPI(health_monitor=monitor, alert_manager=alert_mgr)
    summary = api.get_system_summary()
    
    assert summary["total_alerts"] == 1
    assert len(summary["recent_alerts"]) == 1
    assert summary["recent_alerts"][0]["title"] == "High Latency"

def test_dashboard_api_portfolio_snapshot_mock():
    mock_pm = MockPortfolioManager()
    api = ReadOnlyDashboardAPI(portfolio_manager=mock_pm)
    snapshot = api.get_portfolio_snapshot()
    
    assert snapshot["status"] == "HEALTHY"
    assert snapshot["total_equity"] == 10000.0
    assert "BTCUSDT" in snapshot["positions"]

def test_dashboard_api_portfolio_snapshot_none():
    api = ReadOnlyDashboardAPI(portfolio_manager=None)
    snapshot = api.get_portfolio_snapshot()
    assert snapshot["status"] == "UNAVAILABLE"

def test_dashboard_api_metrics_endpoint():
    monitor = SystemHealthMonitor()
    monitor.record_tick()
    monitor.record_tick()
    monitor.record_error("Sample error")
    
    api = ReadOnlyDashboardAPI(health_monitor=monitor)
    metrics = api.get_metrics_endpoint()
    
    assert metrics["is_alive"] is True
    assert metrics["total_ticks"] == 2
    assert metrics["error_count"] == 1
    assert metrics["alert_count"] == 1
