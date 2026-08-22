from src.core.paper_session import PaperSession
from src.core.trading_engine import PaperTradingEngine


def test_trading_engine() -> None:
    print("[1] ساخت نشست آزمایشی...")

    session = PaperSession(
        session_name="test_engine_session",
        initial_capital=10000.0,
    )

    engine = PaperTradingEngine(session)

    print("[2] تست معامله Long سودده...")

    result = engine.execute_paper_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=50000.0,
        exit_price=51500.0,
        position_size=0.1,
    )

    assert result["gross_pnl"] == 150.0
    assert result["net_pnl"] == 150.0
    assert session.current_capital == 10150.0
    assert len(session.trades) == 1

    print(f"PNL معامله اول: {result['net_pnl']}")
    print(f"سرمایه فعلی: {session.current_capital}")

    print("[3] تست معامله Short زیان‌ده...")

    result_2 = engine.execute_paper_trade(
        symbol="ETHUSDT",
        side="SELL",
        entry_price=3000.0,
        exit_price=3100.0,
        position_size=1.0,
    )

    assert result_2["gross_pnl"] == -100.0
    assert result_2["net_pnl"] == -100.0
    assert session.current_capital == 10050.0
    assert len(session.trades) == 2

    print(f"PNL معامله دوم: {result_2['net_pnl']}")
    print(f"سرمایه نهایی: {session.current_capital}")

    print("[4] تست کارمزد...")

    result_3 = engine.execute_paper_trade(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=50000.0,
        exit_price=50100.0,
        position_size=0.1,
        fees=2.0,
    )

    assert result_3["gross_pnl"] == 10.0
    assert result_3["net_pnl"] == 8.0
    assert session.current_capital == 10058.0

    print(f"PNL خالص پس از کارمزد: {result_3['net_pnl']}")
    print(f"سرمایه پس از کارمزد: {session.current_capital}")

    print("[5] تست ذخیره و بارگذاری نشست...")

    save_path = session.save("data/paper_trades/test_engine_session.json")
    loaded_session = PaperSession.load(save_path)

    assert loaded_session.current_capital == 10058.0
    assert loaded_session.total_pnl == 58.0
    assert len(loaded_session.trades) == 3

    print("ذخیره و بارگذاری موفق بود.")
    print("=== TRADING ENGINE TEST PASSED ===")


if __name__ == "__main__":
    test_trading_engine()
