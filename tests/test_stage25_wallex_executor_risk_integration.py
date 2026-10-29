from src.exchange.wallex_order_executor import WallexOrderExecutor
from src.core.risk_guard import WallexRiskGuard


def test_stage25_blocks_order_when_stop_loss_invalid_for_buy():
    guard = WallexRiskGuard()
    ex = WallexOrderExecutor(dry_run=True, risk_guard=guard)

    r = ex.submit_order_with_risk_guard(
        symbol="TMNUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=2.0,
        price=60000.0,
        capital_tmn=10_000_000.0,
        stop_loss_price=61000.0,  # invalid for BUY
    )
    assert r["success"] is False
    assert r["stage"] == "risk"
    assert r["reason"] == "INVALID_STOP_LOSS_FOR_BUY"


def test_stage25_blocks_order_when_exceeds_max_risk():
    guard = WallexRiskGuard(max_risk_pct_per_trade=0.005)  # 0.5%
    ex = WallexOrderExecutor(dry_run=True, risk_guard=guard)

    r = ex.submit_order_with_risk_guard(
        symbol="TMNUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=10.0,
        price=60000.0,
        capital_tmn=1_000_000.0,
        stop_loss_price=40000.0,  # huge risk
    )
    assert r["success"] is False
    assert r["stage"] == "risk"
    assert r["reason"] == "EXCEEDS_MAX_RISK_PER_TRADE"


def test_stage25_allows_order_and_preserves_stage23_dry_run_contract():
    guard = WallexRiskGuard(max_risk_pct_per_trade=0.02)
    ex = WallexOrderExecutor(dry_run=True, risk_guard=guard)

    r = ex.submit_order_with_risk_guard(
        symbol="TMNUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=2.0,
        price=60000.0,
        capital_tmn=10_000_000.0,
        stop_loss_price=58500.0,
    )

    assert r["success"] is True
    assert r["dry_run"] is True
    assert r["order_id"].startswith("DRY-")
    assert r["payload"]["side"] == "BUY"
    assert r["payload"]["price"] == 60000.0
    assert "risk" in r
    assert r["risk"]["allowed"] is True
