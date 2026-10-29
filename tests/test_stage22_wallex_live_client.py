from src.exchange.wallex_live_client import WallexLiveClient

def test_stage22_dry_run_balance():
    client = WallexLiveClient(api_key="", dry_run=True)
    res = client.get_account_balance()
    assert res["success"] is True
    assert res["mock"] is True
    assert "TMN" in res["balances"]

def test_stage22_ticker_fetch():
    client = WallexLiveClient(dry_run=True)
    res = client.get_ticker("TMNUSDT")
    assert res["success"] is True
    assert res["lastPrice"] > 0
