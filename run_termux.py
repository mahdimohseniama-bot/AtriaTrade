import time
from src.core.paper_live_runner import PaperLiveRunner

def print_header():
    print("==========================================================")
    print("🚀 ATRIATRADE TERMINAL - SMC COMPOUND TRADING ENGINE 🚀")
    print("==========================================================")

def run():
    print_header()
    # Initialize the engine
    runner = PaperLiveRunner()
    
    # Run the main loop
    try:
        while True:
            # Refresh data
            runner.update_market_data()
            
            # Display stats
            capital = runner.get_current_capital()
            print(f"💼 Total Capital: ${capital['total']:.2f}")
            print(f"🔄 Working Capital: ${capital['working']:.2f}")
            print(f"🔒 Vault Balance: ${capital['vault']:.2f}")
            print("----------------------------------------------------------")
            print("🔍 Market Analysis (BTC/USDT & ETH/USDT)...")
            
            # Logic check
            if runner.has_directional_bias():
                print("✅ Trade signal detected, executing...")
                runner.execute_strategy()
            else:
                print("⚠️ Warning: Contradictory directional bias or zone constraint.")
            
            print("==========================================================")
            print("✅ Pipeline active and monitoring...")
            print("==========================================================")
            
            # Wait for next tick
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AtriaTrade terminal...")

if __name__ == "__main__":
    run()
