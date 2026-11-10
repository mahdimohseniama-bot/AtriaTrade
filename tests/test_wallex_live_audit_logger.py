import pytest
import os
import shutil
from src.core.wallex_live_audit_logger import WallexLiveAuditLogger

TEST_LOG_DIR = "tests_tmp_logs"

@pytest.fixture
def audit_logger():
    if os.path.exists(TEST_LOG_DIR):
        shutil.rmtree(TEST_LOG_DIR)
    logger = WallexLiveAuditLogger(log_dir=TEST_LOG_DIR, filename="test_audit.jsonl")
    yield logger
    if os.path.exists(TEST_LOG_DIR):
        shutil.rmtree(TEST_LOG_DIR)

def test_log_single_event(audit_logger):
    payload = {"symbol": "BTC_IRT", "action": "BUY", "amount": 0.05}
    record = audit_logger.log_event("ORDER_SUBMITTED", payload, status="SUCCESS", timestamp=1000.0)
    assert record["event_type"] == "ORDER_SUBMITTED"
    assert record["status"] == "SUCCESS"
    assert record["payload"]["symbol"] == "BTC_IRT"

    events = audit_logger.read_recent_events(limit=5)
    assert len(events) == 1
    assert events[0]["event_type"] == "ORDER_SUBMITTED"

def test_log_multiple_events_and_tail(audit_logger):
    for i in range(15):
        audit_logger.log_event("METRIC_UPDATE", {"index": i}, timestamp=float(i))
    
    events = audit_logger.read_recent_events(limit=5)
    assert len(events) == 5
    assert events[0]["payload"]["index"] == 10
    assert events[-1]["payload"]["index"] == 14

def test_read_non_existent_log():
    logger = WallexLiveAuditLogger(log_dir=TEST_LOG_DIR, filename="non_existent.jsonl")
    events = logger.read_recent_events()
    assert events == []
