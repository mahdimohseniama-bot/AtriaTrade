from src.exchange.wallex_account_fetcher import WallexAccountFetcher

def test_stage14_account_fetcher():
    print("[STAGE 14] WALLEX ACCOUNT FETCHER TEST STARTING...")
    
    # Test Mock Connectivity
    fetcher = WallexAccountFetcher(api_key="MOCK_KEY", api_secret="MOCK_SECRET")
    res = fetcher.fetch_balance("USDT")
    
    assert res["success"] is True
    assert res["balance"] == 1000.0
    assert res["note"] == "MOCK_MODE"
    
    print("[SUCCESS] Stage 14 Wallex Account Fetcher Passed!")

if __name__ == "__main__":
    test_stage14_account_fetcher()
