import time

from src.core.paper_live_runner import PaperTradingLiveRunner


def show_state(runner, title):
    print(f"\n📊 {title}")
    print(f"  موجودی نقدی: {runner.balance:,.0f} RLS")
    print(f"  تعداد پوزیشن‌های باز: {len(runner.open_positions)}")
    print(f"  تعداد رکوردهای تاریخچه: {len(runner.trade_history)}")

    if runner.open_positions:
        print("  پوزیشن‌های باز:")
        for position_id, position in runner.open_positions.items():
            print(f"    - {position_id}: {position}")

    if runner.trade_history:
        print("  آخرین رکورد تاریخچه:")
        print(f"    {runner.trade_history[-1]}")


def make_candle(price):
    return {
        "timestamp": int(time.time()),
        "open": float(price),
        "high": float(price * 1.002),
        "low": float(price * 0.998),
        "close": float(price),
        "volume": 1.0,
    }


def main():
    print("🚀 اجرای تست صحیح BUY/SELL در Paper Trading...")

    symbol = "BTCIRT"
    initial_balance = 500_000_000.0
    base_price = 6_500_000_000.0

    runner = PaperTradingLiveRunner(
        symbol=symbol,
        initial_balance=initial_balance,
    )
    runner.start()

    try:
        # تزریق کندل‌های صعودی برای آماده‌سازی رژیم بازار
        print("\n🕯️ تزریق کندل‌های اولیه...")
        last_candle = None

        for i in range(20):
            price = base_price * (1 + i * 0.001)
            last_candle = make_candle(price)
            result = runner.ingest_candle(last_candle)

            print(
                f"  Candle {i + 1:02d} | "
                f"Price={price:,.0f} | "
                f"Regime={result.get('regime')} | "
                f"Status={result.get('status')}"
            )

        show_state(runner, "وضعیت قبل از BUY")

        # ورود با ۱۰ درصد موجودی
        buy_signal = {
            "side": "BUY",
            "size_pct": 0.10,
        }

        print("\n🟢 ارسال سیگنال BUY...")
        buy_result = runner.process_signal(buy_signal, last_candle)
        print("  نتیجه BUY:", buy_result)

        show_state(runner, "وضعیت بعد از BUY")

        if buy_result.get("status") != "FILLED":
            print("\n⚠️ سیگنال BUY اجرا نشد.")
            print("علت:", buy_result.get("reason", "نامشخص"))
            return

        # افزایش قیمت ۳ درصدی برای تست خروج سودده
        exit_price = last_candle["close"] * 1.03
        exit_candle = make_candle(exit_price)

        runner.ingest_candle(exit_candle)

        sell_signal = {
            "side": "SELL",
        }

        print("\n🔴 ارسال سیگنال SELL...")
        sell_result = runner.process_signal(sell_signal, exit_candle)
        print("  نتیجه SELL:", sell_result)

        show_state(runner, "وضعیت نهایی پس از SELL")

        expected_profit = initial_balance * 0.10 * 0.03

        print("\n🧮 کنترل نتیجه:")
        print(f"  موجودی اولیه: {initial_balance:,.0f} RLS")
        print(f"  سود تقریبی مورد انتظار: {expected_profit:,.0f} RLS")
        print(f"  موجودی نهایی: {runner.balance:,.0f} RLS")
        print(f"  سود واقعی: {runner.balance - initial_balance:,.0f} RLS")

        buy_ok = buy_result.get("status") == "FILLED"
        sell_ok = sell_result.get("status") == "CLOSED"
        balance_ok = runner.balance > initial_balance
        positions_ok = len(runner.open_positions) == 0
        history_ok = len(runner.trade_history) >= 2

        print("\n✅ نتیجه کنترل‌ها:")
        print("  BUY اجرا شد:", buy_ok)
        print("  SELL اجرا شد:", sell_ok)
        print("  موجودی افزایش یافت:", balance_ok)
        print("  پوزیشن باز باقی نماند:", positions_ok)
        print("  تاریخچه ثبت شد:", history_ok)

        if all([buy_ok, sell_ok, balance_ok, positions_ok, history_ok]):
            print("\n🎉 STAGE 2 PASSED")
        else:
            print("\n❌ STAGE 2 FAILED")

    finally:
        runner.stop()
        print("\n🛑 رانر متوقف شد.")


if __name__ == "__main__":
    main()
