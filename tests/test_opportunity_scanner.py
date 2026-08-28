"""Unit tests for Multi-Exchange Opportunity Scanner."""

from src.core.opportunity_scanner import OpportunityScanner


def test_scanner_detects_arbitrage_opportunity():
    scanner = OpportunityScanner(min_spread_pct=1.0)
    prices = {
        "nobitex": 100_000.0,
        "wallex": 103_000.0
    }
    # Gross spread = 3.0%, fees = 2 * 0.2% = 0.4%, Net = 2.6% >= 1.0%
    result = scanner.scan_pair_spread("BTCUSDT", prices, fee_pct=0.2)
    assert result is not None
    assert result["buy_exchange"] == "nobitex"
    assert result["sell_exchange"] == "wallex"
    assert result["net_spread_pct"] == 2.6
    assert result["action"] == "ARBITRAGE_OPPORTUNITY"


def test_scanner_ignores_low_spread():
    scanner = OpportunityScanner(min_spread_pct=1.0)
    prices = {
        "nobitex": 100_000.0,
        "wallex": 100_300.0
    }
    # Gross spread = 0.3%, net is negative after fees -> None
    result = scanner.scan_pair_spread("BTCUSDT", prices, fee_pct=0.2)
    assert result is None


def test_scanner_with_single_exchange():
    scanner = OpportunityScanner(min_spread_pct=0.5)
    prices = {"nobitex": 100_000.0}
    assert scanner.scan_pair_spread("BTCUSDT", prices) is None
