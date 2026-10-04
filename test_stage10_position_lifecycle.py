import sys
from src.core.wallex_live_orchestrator import WallexLiveOrchestrator

def run_stage10_test():
    print("=" * 65)
    print(">>> [STAGE 10] WALLEX POSITION LIFECYCLE & SETTLEMENT TEST")
    print("=" * 65)
    
    orchestrator = WallexLiveOrchestrator()
    print("[*] Initiating Live Trade Setup...")
    init_res = orchestrator.execute_cycle()
    
    assert init_res["status"] == "SUCCESS", "Setup failed"
    entry = init_res["entry_price"]
    tp = init_res["tp"]
    sl = init_res["sl"]
    units = init_res["units"]
    
    print(f"[+] Position Opened: {units} units @ {entry:,.2f} TMN")
    print(f"[+] Active Bounds  : SL={sl:,.2f} | TP={tp:,.2f}")
    
    # Test 1: Price moving inside channel (HOLD)
    mid_price = round((entry + tp) / 2.0, 2)
    hold_tick = orchestrator.process_tick(mid_price)
    print(f"[*] Processing Market Tick @ {mid_price:,.2f} TMN -> Status: {hold_tick['status']} | Action: {hold_tick['action']}")
    assert hold_tick["action"] == "HOLD", "Hold condition check failed"
    
    # Test 2: Price hits TP target (SETTLEMENT)
    print(f"[*] Testing Take Profit Trigger @ {tp:,.2f} TMN...")
    tp_tick = orchestrator.process_tick(tp)
    assert tp_tick["status"] == "CLOSED" and tp_tick["action"] == "TAKE_PROFIT", "TP trigger failed"
    
    print(f"[+] Position Closed: Exit={tp_tick['exit_price']:,.2f} TMN | Realized PnL={tp_tick['pnl']:,.2f} TMN")
    status = tp_tick["account_status"]
    print(f"[+] Balance Update : Active={status['current_capital']:,.2f} TMN | Reserve={status['profit_reserve']:,.2f} TMN")
    
    assert status["profit_reserve"] > 0, "Profit reserve allocation failed"
    
    print("=" * 65)
    print("[SUCCESS] Stage 10 Completed: Position Lifecycle & Settlement Verified.")
    print("=================================================================")

if __name__ == "__main__":
    run_stage10_test()
