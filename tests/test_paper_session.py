import os
import json
from src.core.risk_manager import RiskConfig
from src.core.paper_session import PaperSession

def test_paper_session_lifecycle():
    print("[1] Initializing Paper Trading Session...")
    config = RiskConfig(
        risk_per_trade_pct=1.0,
        stop_loss_pct=1.5,
        take_profit_pct=3.0,
        min_trade_value=10.0
    )
    session = PaperSession(
        session_name="test_run",
        initial_capital=10000.0,
        risk_config=config,
        data_dir="data/paper_trades"
    )

    print("[2] Executing Winning Trade (BTC @ 50,000 -> 51,500)...")
    res1 = session.execute_paper_trade(
        symbol="BTC/USDT",
        side="buy",
        entry_price=50000.0,
        exit_price=51500.0
    )
    assert res1["status"] == "CLOSED", "Trade 1 should be closed successfully"
    assert res1["pnl"] > 0, "Trade 1 must be profitable"
    print(f"-> Trade 1 PNL: {res1['pnl']:.2f}")

    print("[3] Executing Losing Trade (ETH @ 3,000 -> 2,900)...")
    res2 = session.execute_paper_trade(
        symbol="ETH/USDT",
        side="buy",
        entry_price=3000.0,
        exit_price=2900.0
    )
    assert res2["status"] == "CLOSED", "Trade 2 should be closed successfully"
    assert res2["pnl"] < 0, "Trade 2 must have a loss"
    print(f"-> Trade 2 PNL: {res2['pnl']:.2f}")

    print("[4] Validating Session Stats...")
    stats = session.get_session_stats()
    print(f"Total Trades: {stats['total_trades']}, Win Rate: {stats['win_rate_pct']}%")
    assert stats["total_trades"] == 2
    assert stats["win_rate_pct"] == 50.0

    print("[5] Validating JSON persistence...")
    json_path = "data/paper_trades/test_run.json"
    assert os.path.exists(json_path), "JSON history file must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data["trades"]) == 2
    print("-> JSON file verified successfully.")

    print("\n=== PAPER SESSION TEST PASSED ===")

if __name__ == "__main__":
    test_paper_session_lifecycle()
