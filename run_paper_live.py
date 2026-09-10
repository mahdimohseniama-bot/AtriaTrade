import sys
import time
import argparse
from src.core.paper_live_runner import PaperTradingLiveRunner

def parse_args():
    parser = argparse.ArgumentParser(description="AtriaTrade Multi-Exchange Paper Trading Engine")
    parser.add_argument(
        "--exchange", 
        type=str, 
        default="dummy", 
        choices=["dummy", "nobitex", "binance_testnet"],
        help="Target exchange adapter (default: dummy)"
    )
    parser.add_argument(
        "--symbol", 
        type=str, 
        default="BTC/USDT", 
        help="Trading pair symbol (default: BTC/USDT)"
    )
    parser.add_argument(
        "--capital", 
        type=float, 
        default=100.0, 
        help="Initial capital in USD/USDT (default: 100.0)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=3, 
        help="Polling interval in seconds (default: 3)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("\n" + "=" * 65)
    print("      🚀 ATRIATRADE - MULTI-EXCHANGE PAPER RUNNER 🚀")
    print("=" * 65)
    print(f"[*] Target Symbol    : {args.symbol}")
    print(f"[*] Exchange Adapter : {args.exchange.upper()}")
    print(f"[*] Initial Capital  : ${args.capital:.2f}")
    print(f"[*] Capital Model    : 60% Vault (Withdrawable) / 40% Compound")
    print(f"[*] Polling Interval : {args.interval}s")
    print("-" * 65)

    try:
        runner = PaperTradingLiveRunner(
            symbol=args.symbol,
            exchange_name=args.exchange,
            initial_balance=args.capital
        )
        runner.start()
        print("[✓] Multi-Exchange Runner initialized successfully!")
        print("[*] Starting live loop... (Press Ctrl+C to stop)\n")
    except Exception as e:
        print(f"[❌] Initialization Failed: {e}")
        sys.exit(1)

    iteration = 1
    consecutive_network_errors = 0

    while True:
        try:
            # اجرای یک چرخه کامل
            result = runner.step()
            consecutive_network_errors = 0
            
            cur_price = result.get("current_price", 0.0)
            cur_balance = result.get("balance", args.capital)
            regime = result.get("regime", "UNKNOWN")
            open_pos = result.get("open_positions_count", 0)

            print(
                f"[{time.strftime('%H:%M:%S')}] Tick #{iteration:04d} | "
                f"{args.symbol}: ${cur_price:,.2f} | "
                f"Regime: {regime} | Pos: {open_pos} | Capital: ${cur_balance:.2f}"
            )
            
            iteration += 1
            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n" + "=" * 65)
            print("[!] Paper Trading session gracefully stopped.")
            print("=" * 65)
            sys.exit(0)
        except Exception as e:
            consecutive_network_errors += 1
            print(f"[{time.strftime('%H:%M:%S')}] [⚠️ Error #{consecutive_network_errors}]: {e}")
            if consecutive_network_errors >= 5 and args.exchange == "nobitex":
                print("[💡 Tip]: For offline or sanction-proof testing, switch to '--exchange dummy'")
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
