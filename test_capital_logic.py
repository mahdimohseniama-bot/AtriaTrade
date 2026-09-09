import sys
from src.core.capital_manager import CapitalManager

def run_simulation_test():
    print("=" * 55)
    print("      ATRIATRADE CAPITAL LOGIC SIMULATION TEST")
    print("=" * 55)
    
    cm = CapitalManager(initial_capital=100.0, compound_ratio=0.60)
    print(f"Initial State: Working=${cm.get_working_capital():.2f} | Vault=${cm.get_vault_balance():.2f} | Total=${cm.get_total_capital():.2f}\n")
    
    # Trade 1: Loss of $10
    print("[1] Simulating Loss of $10.00...")
    cm.record_trade_result(net_pnl=-10.0)
    print(f"    Working: ${cm.get_working_capital():.2f} (Expected: $90.00)")
    print(f"    Vault:   ${cm.get_vault_balance():.2f} (Expected: $0.00)")
    print(f"    Total:   ${cm.get_total_capital():.2f} (Expected: $90.00)\n")
    
    # Trade 2: Recovery + Profit of $20 (10 to recover, 10 split 60/40)
    print("[2] Simulating Profit of $20.00 (Drawdown recovery + Split)...")
    cm.record_trade_result(profit=20.0)
    print(f"    Working: ${cm.get_working_capital():.2f} (Expected: $106.00 -> 90+10+6)")
    print(f"    Vault:   ${cm.get_vault_balance():.2f} (Expected: $4.00   -> 40% of 10)")
    print(f"    Total:   ${cm.get_total_capital():.2f} (Expected: $110.00)\n")
    
    # Trade 3: Pure Profit of $50 (Split 60% compound / 40% vault)
    print("[3] Simulating Pure Profit of $50.00...")
    cm.record_trade_result(net_pnl=50.0)
    print(f"    Working: ${cm.get_working_capital():.2f} (Expected: $136.00 -> 106+30)")
    print(f"    Vault:   ${cm.get_vault_balance():.2f} (Expected: $24.00  -> 4+20)")
    print(f"    Total:   ${cm.get_total_capital():.2f} (Expected: $160.00)\n")
    
    # Verification assertions
    assert cm.get_working_capital() == 136.0, "Working capital mismatch!"
    assert cm.get_vault_balance() == 24.0, "Vault balance mismatch!"
    assert cm.get_total_capital() == 160.0, "Total capital mismatch!"
    
    print("=" * 55)
    print(" [SUCCESS] All Capital Management calculations verified!")
    print("=" * 55)

if __name__ == "__main__":
    run_simulation_test()
