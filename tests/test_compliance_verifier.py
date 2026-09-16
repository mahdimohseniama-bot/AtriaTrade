from src.core.compliance_verifier import ComplianceVerifier


def test_compliance_verifier_success():
    verifier = ComplianceVerifier(min_notional=10.0, max_notional=50000.0, max_price_deviation_pct=0.05)

    valid_order = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "price": 50100.0,
        "amount": 0.1
    }
    # Notional = 5010.0, deviation = 0.2% <= 5%
    is_valid, reason = verifier.verify_order(valid_order, current_market_price=50000.0)
    assert is_valid
    assert reason is None


def test_compliance_verifier_violations():
    verifier = ComplianceVerifier(min_notional=10.0, max_notional=1000.0, max_price_deviation_pct=0.05)

    # 1. Below min notional
    tiny_order = {"price": 100.0, "amount": 0.05, "type": "LIMIT"}  # Notional = 5.0 < 10.0
    is_valid, reason = verifier.verify_order(tiny_order, current_market_price=100.0)
    assert not is_valid
    assert "below minimum allowed" in reason

    # 2. Exceeds max notional
    huge_order = {"price": 100.0, "amount": 20.0, "type": "LIMIT"}  # Notional = 2000.0 > 1000.0
    is_valid, reason = verifier.verify_order(huge_order, current_market_price=100.0)
    assert not is_valid
    assert "exceeds maximum allowed" in reason

    # 3. Fat-finger price deviation (Price 120 vs Market 100 -> 20% deviation > 5%)
    bad_price_order = {"price": 120.0, "amount": 2.0, "type": "LIMIT"}
    is_valid, reason = verifier.verify_order(bad_price_order, current_market_price=100.0)
    assert not is_valid
    assert "deviates" in reason
