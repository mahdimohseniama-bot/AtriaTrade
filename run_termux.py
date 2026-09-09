import sys
import time
import os
from src.core.capital_manager import CapitalManager
from src.core.live_pipeline import LiveTradingPipeline

def clear_screen():
    os.system('clear')

def main():
    clear_screen()
    print("=" * 60)
    print("🚀  ATRIATRADE TERMINAL - SMC COMPOUND TRADING ENGINE  🚀")
    print("=" * 60)
    
    # راه‌اندازی ماژول مدیریت سرمایه (۶۰٪ کامپاند، ۴۰٪ سیو سود)
    cap_mgr = CapitalManager(initial_capital=100.0, save_ratio=0.40, compound_ratio=0.60)
    pipeline = LiveTradingPipeline(capital_manager=cap_mgr, min_score=60.0)

    print(f"\n💼 [وضعیت حساب]")
    print(f"💵 سرمایه اولیه کل: ${cap_mgr.get_total_capital():.2f}")
    print(f"🔄 سرمایه در گردش فعال (Trading): ${cap_mgr.get_working_capital():.2f}")
    print(f"🔒 کیف پول ذخیره امن (Vault): ${cap_mgr.get_vault_balance():.2f}")
    print("-" * 60)
    print("🔍 در حال تحلیل ساختار مارکت کریپتو فیوچرز (BTC/USDT & ETH/USDT)...")
    time.sleep(1)

    # شبیه‌ساز کندل‌های لایو بازار با ستاپ برگشتی و FVG صعودی روی BTC
    sample_btc_candles = [
        {"open": 64200, "high": 64500, "low": 64100, "close": 64400},
        {"open": 64400, "high": 64600, "low": 63900, "close": 63950},
        {"open": 63950, "high": 64000, "low": 63500, "close": 63600}, # سوییپ کف
        {"open": 63600, "high": 64800, "low": 63550, "close": 64750}, # کندل پرقدرت و ایجاد FVG
        {"open": 64750, "high": 65200, "low": 64600, "close": 65100}
    ]

    trade_result = pipeline.analyze_and_execute("BTC/USDT", sample_btc_candles)
    
    if trade_result and trade_result.get("status") == "ORDER_GENERATED":
        print("\n🎯 [سیگنال هوشمند تایید شد!]")
        print(f"🔹 نماد: {trade_result['symbol']}")
        print(f"🔹 جهت پوزیشن: {trade_result['direction']} ({trade_result['confidence']} - امتیاز: {trade_result['score']}/100)")
        print(f"🔹 فاکتورهای همگرایی: {', '.join(trade_result['confluences'])}")
        print(f"📍 نقطه ورود: ${trade_result['entry_price']:.2f}")
        print(f"🛑 حد ضرر (SL): ${trade_result['stop_loss']:.2f}")
        print(f"🎯 حد سود (TP): ${trade_result['take_profit']:.2f}")
        
        sizing = trade_result['sizing']
        print(f"\n⚙️ [تنظیمات مدیریت ریسک و اهرم داینامیک]")
        print(f"⚡ اهرم محاسبه‌شده: {sizing['effective_leverage']:.1f}x")
        print(f"💰 مارجین درگیر: ${sizing['allocated_margin']:.2f}")
        print(f"📦 حجم اسمی پوزیشن: ${sizing['nominal_position_value']:.2f}")
        print(f"⚠️ حداکثر ریسک معامله: ${sizing['potential_loss']:.2f} ({sizing['risk_pct_of_equity']*100:.1f}%)")

        # تست عملکرد سیستم سود مرکب (شبیه‌سازی برخورد به TP با سود ۶۰ دلاری)
        print("\n" + "=" * 60)
        print("📈 [شبیه‌سازی رسیدن معامله به تارگت سود]")
        simulated_profit = 60.0
        cap_mgr.process_trade_profit(simulated_profit)
        
        print(f"🎉 سود خالص معامله: +${simulated_profit:.2f}")
        print(f"✅ اضافه شده به سرمایه در گردش (۶۰٪ برای معامله بعدی): +${simulated_profit * 0.6:.2f}")
        print(f"🛡️ ذخیره شده در والت امن (۴۰٪ سیو قطعی): +${simulated_profit * 0.4:.2f}")
        print("-" * 60)
        print(f"🔥 سرمایه در گردش جدید برای رشد تصاعدی: ${cap_mgr.get_working_capital():.2f}")
        print(f"💎 موجودی کیف پول امن (Vault): ${cap_mgr.get_vault_balance():.2f}")
        print(f"👑 کل دارایی رشد یافته: ${cap_mgr.get_total_capital():.2f}")
    else:
        print(f"\n⚠️ شرایط ورود مهیا نشد: {trade_result.get('reason', 'نامشخص')}")

    print("\n" + "=" * 60)
    print("✅ سیستم پایپ‌لاین آماده اتصال به دیتای زنده صرافی و استارت ترید است.")
    print("=" * 60)

if __name__ == "__main__":
    main()
