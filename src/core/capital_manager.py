import json
import os
from datetime import datetime

class CapitalManager:
    def __init__(self, initial_capital=100.0, data_file="data/capital_state.json"):
        self.initial_capital = initial_capital
        self.data_file = data_file
        self.current_capital = initial_capital
        self.profit_reserve = 0.0
        self.load_state()

    def load_state(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.initial_capital = data.get("initial_capital", self.initial_capital)
                    self.current_capital = data.get("current_capital", self.initial_capital)
                    self.profit_reserve = data.get("profit_reserve", 0.0)
            except Exception as e:
                print(f"[!] Error loading state: {e}")

    def save_state(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data = {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "profit_reserve": self.profit_reserve,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def record_trade_result(self, pnl: float):
        if pnl > 0:
            self.profit_reserve += pnl
            print(f"[+] Trade Profit: +${pnl:.2f} -> Sent to Profit Reserve!")
        else:
            self.current_capital += pnl  
            print(f"[-] Trade Loss: ${pnl:.2f} -> Deducted from Capital.")
        
        self.save_state()

    def get_status(self):
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "profit_reserve": self.profit_reserve,
            "total_value": self.current_capital + self.profit_reserve
        }

if __name__ == "__main__":
    cm = CapitalManager(initial_capital=100.0)
    print("Initial Status:", cm.get_status())
    cm.record_trade_result(5.0)
    print("After Profit Status:", cm.get_status())
