import sys
from src.core.spread_fee_filter import SpreadFeeFilter

def test_spread_filter():
    print("[STAGE 11] SPREAD & FEE FILTER TEST STARTING...")
    flt = SpreadFeeFilter(max_spread_pct=0.30, taker_fee_pct=0.2)

    # Test Case 1: Healthy low spread
    res1 = flt.evaluate_spread(best_bid=1000000.0, best_ask=1001500.0)
    assert res1["allowed"] is True, f"Expected True but got {res1}"
    assert res1["spread_pct"] == 0.15

    # Test Case 2: Unhealthy high spread
    res2 = flt.evaluate_spread(best_bid=1000000.0, best_ask=1005000.0)
    assert res2["allowed"] is False, f"Expected False but got {res2}"
    assert res2["reason"] == "SPREAD_TOO_HIGH"

    # Test Case 3: Inverted or zero book
    res3 = flt.evaluate_spread(best_bid=0.0, best_ask=1000.0)
    assert res3["allowed"] is False

    print(f"[SUCCESS] Stage 11 Spread Filter Passed! Low spread: {res1['spread_pct']}%, High spread: {res2['spread_pct']}%")

if __name__ == "__main__":
    test_spread_filter()
