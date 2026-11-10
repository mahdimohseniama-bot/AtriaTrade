import pytest
from src.core.alert_notifier import AlertNotifier

def test_alert_notifier_dispatch_and_history():
    notifier = AlertNotifier()
    success = notifier.notify(
        title="POSITION_CLOSED",
        message="Take Profit reached at 67000",
        level="INFO",
        meta={"symbol": "BTCUSDT", "pnl": 2000.0}
    )
    assert success is True
    assert len(notifier.history) == 1
    last = notifier.get_last_alert()
    assert last["title"] == "POSITION_CLOSED"
    assert last["meta"]["pnl"] == 2000.0
    assert last["level"] == "INFO"

def test_alert_notifier_warning_critical():
    notifier = AlertNotifier()
    notifier.notify("RISK_LIMIT", "Daily drawdown exceeded", level="CRITICAL")
    assert notifier.get_last_alert()["level"] == "CRITICAL"
