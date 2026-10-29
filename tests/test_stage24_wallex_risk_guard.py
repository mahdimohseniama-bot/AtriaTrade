from src.core.risk_guard import WallexRiskGuard

def test_stage24_guard_allows_valid_order():
    guard = WallexRiskGuard(max_risk_pct_per_trade=0.02)
    # Capital: 10,000,000 TMN, Entry: 60,000, SL: 58,000, Qty: 5.0 (Notional: 300,000 TMN -> wait, entry*qty = 300,000? Let's check notional min)
    # Let's use Capital: 10,000,000 TMN, Entry: 60,000 TMN, Qty: 5.0 -> Notional = 300,000 TMN (Above 100k min)
    # Risk = abs(60000 - 58500) * 5 = 1500 * 5 = 7500 TMN. Max allowed risk = 10M * 0.02 = 200,000 TMN. Allowed!
    res = guard.evaluate_order(
        capital=10000000.0,
        entry_price=60000.0,
        stop_loss_price=58500.0,
        quantity=5.0,
        side="BUY"
    )
    assert res["allowed"] is True

def test_stage24_guard_rejects_excessive_risk():
    guard = WallexRiskGuard(max_risk_pct_per_trade=0.01)
    # Huge risk: entry 60,000, SL 40,000, qty 10.0 -> Risk = 20,000 * 10 = 200,000. Capital 1M -> max allowed risk = 10,000
    res = guard.evaluate_order(
        capital=1000000.0,
        entry_price=60000.0,
        stop_loss_price=40000.0,
        quantity=10.0,
        side="BUY"
    )
    assert res["allowed"] is False
    assert res["reason"] == "EXCEEDS_MAX_RISK_PER_TRADE"

def test_stage24_circuit_breaker_blocks_trading():
    guard = WallexRiskGuard(max_daily_drawdown_pct=0.05)
    guard.record_loss(600000.0, current_capital=10000000.0) # 6% loss -> trips breaker
    assert guard.circuit_breaker_tripped is True
    
    res = guard.evaluate_order(
        capital=10000000.0,
        entry_price=60000.0,
        stop_loss_price=59000.0,
        quantity=2.0,
        side="BUY"
    )
    assert res["allowed"] is False
    assert res["reason"] == "CIRCUIT_BREAKER_TRIPPED"
