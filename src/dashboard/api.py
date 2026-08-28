from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.core.monitoring import SystemHealthMonitor, SystemAlertManager

class ReadOnlyDashboardAPI:
    """
    API فقط‌خواندنی (Read-Only) جهت استخراج وضعیت زنده سیستم،
    مانیتورینگ هشدارها، پوزیشن‌ها و سلامت بات ترید.
    """
    def __init__(
        self,
        health_monitor: Optional[SystemHealthMonitor] = None,
        alert_manager: Optional[SystemAlertManager] = None,
        portfolio_manager: Optional[Any] = None
    ):
        self.health_monitor = health_monitor or SystemHealthMonitor()
        self.alert_manager = alert_manager or self.health_monitor.alert_manager
        self.portfolio_manager = portfolio_manager

    def get_system_summary(self) -> Dict[str, Any]:
        """خلاصه وضعیت کلی سیستم شامل سلامت و هشدارها"""
        health = self.health_monitor.get_health_status()
        alerts = self.alert_manager.get_alerts()
        recent_alerts = alerts[-10:] if alerts else []

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "total_alerts": len(alerts),
            "recent_alerts": recent_alerts,
            "mode": "PAPER_TRADING_READ_ONLY"
        }

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """دریافت آخرین وضعیت پورتفولیو در صورت اتصال به PortfolioManager"""
        if self.portfolio_manager is None:
            return {
                "status": "UNAVAILABLE",
                "message": "Portfolio manager is not attached.",
                "positions": {},
                "total_balance": 0.0
            }
        
        # اگر پورتفولیو منیجر متد get_portfolio_summary داشت فراخوانی می‌کنیم
        if hasattr(self.portfolio_manager, "get_portfolio_summary"):
            return self.portfolio_manager.get_portfolio_summary()
        elif hasattr(self.portfolio_manager, "positions"):
            return {
                "status": "AVAILABLE",
                "positions": getattr(self.portfolio_manager, "positions", {}),
                "balance": getattr(self.portfolio_manager, "balance", 0.0)
            }
        
        return {"status": "UNKNOWN_INTERFACE"}

    def get_metrics_endpoint(self) -> Dict[str, Any]:
        """اندپوینت تجمیعی جهت ارائه متریک‌ها به مانیتورینگ خارجی"""
        health = self.health_monitor.get_health_status()
        return {
            "is_alive": health.get("is_alive", False),
            "status": health.get("status", "UNKNOWN"),
            "total_ticks": health.get("total_ticks", 0),
            "error_count": health.get("error_count", 0),
            "alert_count": len(self.alert_manager.get_alerts())
        }
