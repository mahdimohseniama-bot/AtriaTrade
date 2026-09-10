import sys
import time
from src.core.paper_live_runner import PaperTradingLiveRunner

def main():
    print("=" * 60)
    print("🚀 [AtriaTrade] Modular Multi-Exchange Live/Paper Trading Engine")
    print("💎 Rule: 60% Secure Vault Wallet | 40% Account Compound Growth")
    print("=" * 60)

    exchange_choice = "nobitex"
    print(f"📡 Initializing connection to Exchange: [{exchange_choice.upper()}]...")
    
    runner = PaperTradingLiveRunner(
        symbol="BTC/USDT",
        exchange_name=exchange_choice,
        initial_capital=100.0
    )

    ticker = runner.exchange.get_ticker("BTC/USDT")
    print(f"✅ Connected! Ticker [{ticker['symbol']}]: ${ticker['last_price']:,.2f}")
    print(f"💰 Initial Capital: ${runner.capital_manager.current_capital:.2f}")
    print(f"🔒 Initial Vault:   ${runner.capital_manager.vault_balance:.2f}")
    print("-" * 60)

    # Step 1: Open Position
    print("\n[1] 🟢 Opening BUY Position: 0.0003 BTC...")
    pos = runner.open_position("BTC/USDT", side="BUY", amount=0.0003)
    if pos:
        print(f"    ✔ Order Executed! ID: {pos['order_id']} | Price: ${pos['entry_price']:,.2f}")
    else:
        print("    ❌ Position rejected by Risk Manager!")
        return

    time.sleep(1)

    # Step 2: Simulating Trade Close with Gain
    simulated_exit = 75000.0  # +$10,000 price movement
    print(f"\n[2] 🔴 Closing BUY Position @ ${simulated_exit:,.2f}...")
    trade = runner.close_position("BTC/USDT", exit_price=simulated_exit)

    print(f"    ✔ Trade Closed! Realized PnL: +${trade['pnl']:.2f}")
    
    summary = runner.get_summary()
    print("\n" + "=" * 60)
    print("📊 PORTFOLIO & CAPITAL SUMMARY:")
    print(f"    🏦 Active Trading Capital (Compound): ${summary['current_capital']:.2f}")
    print(f"    🛡️  Secure Vault Balance (60% Profit): ${summary['vault_balance']:.2f}")
    print(f"    📈 Total Accumulated Wealth:          ${summary['total_wealth']:.2f}")
    print("=" * 60)
    print("🎉 Trade cycle completed successfully without errors!")

if __name__ == "__main__":
    main()
