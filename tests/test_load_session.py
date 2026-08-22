from src.core.paper_session import PaperSession
import os

def test_load_and_continue_session():
    # ساخت و ذخیره اولیه
    s1 = PaperSession("session1", 10000.0)
    s1.record_trade("BTC/USDT", "BUY", 50000.0, 51000.0, 1.0, 1000.0)
    path = "data/paper_trades/session1.json"
    s1.save(path)
    
    # بارگذاری و ادامه
    s2 = PaperSession.load(path)
    assert s2.current_capital == 11000.0
    s2.record_trade("ETH/USDT", "SELL", 3000.0, 2900.0, 1.0, 100.0)
    
    print("=== LOAD SESSION TEST PASSED ===")

if __name__ == "__main__":
    test_load_and_continue_session()
