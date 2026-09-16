from typing import Dict

class CapitalManager:
    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = float(initial_capital)
        self.current_capital = float(initial_capital)
        self.profit_reserve = 0.0

    def record_trade_result(self, net_pnl: float):
        """ثبت سود/زیان معامله و مدیریت خودکار تفکیک سود و جبران سرمایه"""
        if net_pnl > 0:
            # اگر سرمایه قبلاً دچار افت شده باشد، اول اصل سرمایه جبران می‌شود
            shortfall = self.initial_capital - self.current_capital
            if shortfall > 0:
                recovery_amount = min(shortfall, net_pnl)
                self.current_capital += recovery_amount
                remaining_profit = net_pnl - recovery_amount
                self.profit_reserve += remaining_profit
                print(f" [+] Recovered ${recovery_amount:.4f} to Capital. Rest ${remaining_profit:.4f} -> Profit Reserve.")
            else:
                # سرمایه کامل است، تمام سود مستقیماً به صندوق سود منتقل می‌شود
                self.profit_reserve += net_pnl
                print(f" [+] Profit ${net_pnl:.4f} transferred directly to Profit Reserve.")
        elif net_pnl < 0:
            loss = abs(net_pnl)
            self.current_capital -= loss
            print(f" [-] Trade Loss: -${loss:.4f} deducted from Active Capital.")

    def get_status(self) -> Dict[str, float]:
        """گزارش وضعیت تفکیکی دارایی"""
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "profit_reserve": self.profit_reserve,
            "total_value": self.current_capital + self.profit_reserve
        }
