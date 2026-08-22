import time
from src.core.capital_manager import CapitalManager
from src.exchange_simulator import ExchangeSimulator

class TraderEngine:
    def __init__(self, capital_manager: CapitalManager, exchange: ExchangeSimulator):
        self.capital_mgr = capital_manager
        self.exchange = exchange
        self.active_position = None

    def run_simulated_trade(self, symbol="BTCUSDT"):
        print("\n" + "="*45)
        print(f"[*] Starting Simulated Trade Cycle for {symbol}")
        print("="*45)
        
        # 1. دریافت قیمت ورود و باز کردن پوزیشن خرید
        entry_order = self.exchange.execute_order(symbol, "MARKET", amount=0.01, side="buy")
        entry_price = entry_order["price"]
        self.active_position = {
            "symbol": symbol,
            "entry_price": entry_price,
            "amount": entry_order["amount"]
        }
        print(f"[>] Position Opened: Bought {self.active_position['amount']} {symbol} at ${entry_price:.2f}")
        
        # شبیه‌سازی گذشت زمان (نوسان در بازار)
        print("[*] Waiting for market movement...")
        time.sleep(1)
        
        # 2. دریافت قیمت خروج و فروش پوزیشن
        exit_order = self.exchange.execute_order(symbol, "MARKET", amount=0.01, side="sell")
        exit_price = exit_order["price"]
        
        # محاسبه سود یا زیان (PnL)
        price_diff = exit_price - entry_price
        pnl = price_diff * self.active_position["amount"]
        
        print(f"[<] Position Closed: Sold at ${exit_price:.2f}")
        print(f"[*] Trade Result (PnL): ${pnl:+.4f}")
        
        # 3. ثبت سود/زیان در مدیر سرمایه (جداسازی خودکار سود)
        self.capital_mgr.record_trade_result(round(pnl, 2))
        self.active_position = None
        
        # نمایش وضعیت به‌روز شده حساب
        status = self.capital_mgr.get_status()
        print("\n--- Updated Financial State ---")
        print(f"Initial Capital : ${status['initial_capital']:.2f}")
        print(f"Active Capital  : ${status['current_capital']:.2f}")
        print(f"Profit Reserve  : ${status['profit_reserve']:.2f}")
        print(f"Total Net Worth : ${status['total_value']:.2f}")
        print("="*45 + "\n")

if __name__ == "__main__":
    cm = CapitalManager(initial_capital=100.0)
    ex = ExchangeSimulator()
    engine = TraderEngine(capital_manager=cm, exchange=ex)
    
    # اجرای دو ترید شبیه‌سازی‌شده آزمایشی
    engine.run_simulated_trade("BTCUSDT")
    engine.run_simulated_trade("BTCUSDT")
