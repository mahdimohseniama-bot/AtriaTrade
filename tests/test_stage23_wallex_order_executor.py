from src.exchange.wallex_order_executor import WallexOrderExecutor


def test_stage23_rejects_invalid_side():
    ex = WallexOrderExecutor(dry_run=True)
    r = ex.validate_order("HOLD", "MARKET", 1.0, 100.0)
    assert r["ok"] is False and r["reason"] == "INVALID_SIDE"


def test_stage23_rejects_zero_quantity():
    ex = WallexOrderExecutor(dry_run=True)
    r = ex.validate_order("BUY", "MARKET", 0.0, 100.0)
    assert r["ok"] is False and r["reason"] == "NON_POSITIVE_QUANTITY"


def test_stage23_limit_requires_price():
    ex = WallexOrderExecutor(dry_run=True)
    r = ex.validate_order("BUY", "LIMIT", 1.0, None)
    assert r["ok"] is False and r["reason"] == "LIMIT_PRICE_REQUIRED"


def test_stage23_below_min_notional():
    ex = WallexOrderExecutor(dry_run=True, min_notional_tmn=100000.0)
    r = ex.validate_order("BUY", "LIMIT", 0.001, 1000.0)
    assert r["ok"] is False and r["reason"] == "BELOW_MIN_NOTIONAL"


def test_stage23_dry_run_order_success():
    ex = WallexOrderExecutor(dry_run=True)
    r = ex.submit_order("TMNUSDT", "BUY", "LIMIT", 2.0, 60000.0)
    assert r["success"] is True
    assert r["dry_run"] is True
    assert r["order_id"].startswith("DRY-")
    assert r["payload"]["side"] == "BUY"
    assert r["payload"]["price"] == 60000.0
