#!/usr/bin/env python3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.paper_factory import PaperExchangeFactory
from src.core.capital_manager import CapitalManager

def run_simulation():
    print("=" * 65)
    print("💎 [AtriaTrade] Wallex Paper Execution & 60/40 Split Engine")
    print("=" * 65)

    # 1. مقداردهی اولیه شبیه‌ساز والکس
    initial_balances = {
        "tm": 100_000_000.0,
        "usdt": 2000.0,
        "btc": 0.0,
        "eth": 0.0
    }
    wallex = PaperExchangeFactory.create_adapter("wallex", initial_balances=initial_balances)
    cap_mgr = CapitalManager(initial_capital=100.0)

    print(f"📊 [Initial Balances] TM: {wallex.get_balance('tm'):,.0f} | USDT: {wallex.get_balance('usdt'):,.2f} | BTC: {wallex.get_balance('btc'):.4f}")
    print(f"💼 [Capital Manager] Active Capital: ${cap_mgr.current_capital:.2f} | Profit Reserve (Vault): ${cap_mgr.profit_reserve:.2f}\n")

    # پارامترهای ترید: خرید 0.015 بیت کوین
    btc_amount = 0.015
    buy_price = 95_000.0
    cost = buy_price * btc_amount  # 1,425 USDT (متناسب با موجودی)
    wallex.set_market_price("BTCUSDT", buy_price)
    
    print(f"🔵 [Signal Generated] BUY {btc_amount} BTC @ ${buy_price:,.2f} (Cost: ${cost:,.2f} USDT)")
    buy_order = wallex.place_order("BTCUSDT", side="buy", order_type="market", amount=btc_amount)
    
    if buy_order.get("status") != "success":
        print(f"❌ [Execution Aborted] Buy order failed: {buy_order.get('message', 'Unknown')}")
        return

    ref_buy = buy_order.get("result", {}).get("clientOrderId", "N/A")
    print(f"   -> Status: {buy_order.get('status')} | Ref: {ref_buy}")
    print(f"   -> Post-Buy Balances: USDT=${wallex.get_balance('usdt'):,.2f} | BTC={wallex.get_balance('btc'):.4f}\n")

    time.sleep(0.3)

    # تارگت خروج و فروش (Take Profit روی 100,000 تتر)
    sell_price = 100_000.0
    sell_value = sell_price * btc_amount  # 1,500 USDT
    wallex.set_market_price("BTCUSDT", sell_price)

    print(f"🟢 [Take Profit Hit] SELL {btc_amount} BTC @ ${sell_price:,.2f} (Value: ${sell_value:,.2f} USDT)")
    sell_order = wallex.place_order("BTCUSDT", side="sell", order_type="market", amount=btc_amount)
    
    if sell_order.get("status") != "success":
        print(f"❌ [Execution Aborted] Sell order failed: {sell_order.get('message', 'Unknown')}")
        return

    ref_sell = sell_order.get("result", {}).get("clientOrderId", "N/A")
    print(f"   -> Status: {sell_order.get('status')} | Ref: {ref_sell}")
    print(f"   -> Post-Sell Balances: USDT=${wallex.get_balance('usdt'):,.2f} | BTC={wallex.get_balance('btc'):.4f}\n")

    # محاسبه سود خالص واقعی
    net_pnl = sell_value - cost  # +$75 USDT سود خالص
    cap_mgr.record_trade_result(net_pnl=net_pnl)
    status = cap_mgr.get_status()

    vault_portion = net_pnl * 0.60
    compound_portion = net_pnl * 0.40

    print("=" * 65)
    print("📈 [CAPITAL MANAGER REPORT - 60/40 SPLIT]")
    print(f"   💰 Realized Trade Net PnL           : +${net_pnl:,.2f} USDT")
    print(f"   💵 60% Withdrawable Vault Reserve   : +${vault_portion:,.2f} USDT")
    print(f"   🔄 40% Working Capital Compound     : +${compound_portion:,.2f} USDT")
    print(f"   🏦 Profit Reserve (Vault Total)     : ${status.get('profit_reserve', 0.0):,.2f}")
    print(f"   🚀 Working Trading Capital          : ${status.get('current_capital', 0.0):,.2f}")
    print(f"   💎 Total Portfolio Equity           : ${status.get('total_value', 0.0):,.2f}")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
