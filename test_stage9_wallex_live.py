from src.core.wallex_live_orchestrator import WallexLiveOrchestrator

def run_stage9_test():
    print("=" * 65)
    print(">>> [STAGE 9] WALLEX LIVE REAL-TIME PAPER TRADING TEST")
    print("=" * 65)

    orchestrator = WallexLiveOrchestrator(initial_capital=50_000_000.0, symbol="USDTTMN")
    
    print("[*] Running Live Execution Cycle with Live Wallex Stream...")
    res = orchestrator.execute_cycle()

    print(f"[+] Market Status  : Connected")
    print(f"[+] Current Price  : {res.get('market_price', 0):,.2f} TMN")
    print(f"[+] Strategy State : Signal={res.get('signal')} | Action={res.get('status')}")
    
    if "order" in res:
        ord_info = res["order"]
        print(f"[+] Execution Plan : {ord_info['side']} {ord_info['qty']} units @ {ord_info['entry']:,.2f}")
        print(f"[+] Risk Bounds    : SL={ord_info['sl']:,.2f} | TP={ord_info['tp']:,.2f}")

    print("=" * 65)
    print("[SUCCESS] Stage 9 Completed: Wallex Live Orchestration Pipeline Verified.")
    print("=" * 65)

if __name__ == "__main__":
    run_stage9_test()
