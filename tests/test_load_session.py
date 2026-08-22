from src.core.paper_session import PaperSession

def test_load_and_continue_session():
    print("[1] Creating and running initial session...")
    session_name = "test_reload_run"
    
    # Run session 1
    session1 = PaperSession(session_name=session_name, initial_capital=10000.0)
    t1 = session1.execute_trade("BTC/USDT", "buy", 50000.0, 51500.0)
    print(f"-> Trade 1 PNL: {t1['pnl']:.2f}")
    
    stats1 = session1.get_session_stats()
    print(f"Stats after Run 1 -> Trades: {stats1['total_trades']}, Capital: {stats1['current_capital']}")

    print("\n[2] Loading session from disk...")
    session2 = PaperSession.load_session(session_name)
    stats2 = session2.get_session_stats()
    
    print(f"Loaded Stats -> Trades: {stats2['total_trades']}, Capital: {stats2['current_capital']}")
    assert stats2['total_trades'] == 1, "Loaded session should have 1 trade!"

    print("\n[3] Executing new trade on reloaded session...")
    t2 = session2.execute_trade("SOL/USDT", "buy", 100.0, 110.0)
    print(f"-> Trade 2 PNL: {t2['pnl']:.2f}")
    
    final_stats = session2.get_session_stats()
    print(f"Final Stats -> Total Trades: {final_stats['total_trades']}, Win Rate: {final_stats['win_rate_pct']}%")
    assert final_stats['total_trades'] == 2, "Reloaded session should now have 2 trades!"

    print("\n=== LOAD SESSION TEST PASSED ===")

if __name__ == "__main__":
    test_load_and_continue_session()
