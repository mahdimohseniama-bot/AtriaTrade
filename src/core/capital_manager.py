from typing import Dict

class CapitalManager:
    """
    سیستم جامع مدیریت سرمایه ۶۰/۴۰ (Compound / Vault)
    سازگار کامل با ترمینال رانر Termux و متدهای نام‌گذاری گوناگون
    """

    def __init__(
        self,
        initial_balance: float = 1000.0,
        reinvest_ratio: float = 0.60,
        vault_ratio: float = 0.40,
        **kwargs
    ):
        capital = kwargs.get("initial_capital", initial_balance)
        self.initial_capital = float(capital)
        self.initial_balance = float(capital)
        self.current_capital = float(capital)
        self.working_capital = float(capital)
        
        self.reinvest_ratio = float(kwargs.get("compound_ratio", reinvest_ratio))
        self.vault_ratio = float(kwargs.get("save_ratio", vault_ratio))
        self.profit_reserve = 0.0
        self.vault_balance = 0.0

    # دسترسی به سرمایه کل
    def get_total_capital(self) -> float:
        """مجموع کل ارزش: سرمایه فعال + گاوصندوق"""
        return self.current_capital + self.vault_balance

    # دسترسی به سرمایه فعال در گردش (Trading / Working)
    def get_working_capital(self) -> float:
        """سرمایه فعال در گردش معاملاتی"""
        return self.current_capital

    def get_current_capital(self) -> float:
        return self.current_capital

    def get_available_capital(self) -> float:
        return self.current_capital

    # دسترسی به گاوصندوق سیو سود (Vault)
    def get_vault_balance(self) -> float:
        """موجودی سیو سود در گاوصندوق"""
        return self.vault_balance

    def get_profit_reserve(self) -> float:
        return self.profit_reserve

    def get_initial_capital(self) -> float:
        return self.initial_capital

    def record_trade_result(self, net_pnl: float):
        """
        ثبت نتیجه معامله:
        - اگر سود باشد: ابتدا جبران افت سرمایه اولیه، سپس تقسیم ۶۰٪ کامپاند و ۴۰٪ گاوصندوق
        - اگر ضرر باشد: کسر مستقیم از سرمایه فعال در گردش
        """
        if net_pnl > 0:
            shortfall = self.initial_capital - self.current_capital
            if shortfall > 0:
                recovery_amount = min(shortfall, net_pnl)
                self.current_capital += recovery_amount
                remaining_profit = net_pnl - recovery_amount
                
                to_compound = remaining_profit * self.reinvest_ratio
                to_save = remaining_profit * self.vault_ratio
                self.current_capital += to_compound
                self.profit_reserve += to_save
                self.vault_balance += to_save
                print(f" [+] Recovered: ${recovery_amount:.2f} | Compound: ${to_compound:.2f} | Vault: ${to_save:.2f}")
            else:
                to_compound = net_pnl * self.reinvest_ratio
                to_save = net_pnl * self.vault_ratio
                self.current_capital += to_compound
                self.profit_reserve += to_save
                self.vault_balance += to_save
                print(f" [+] Profit: ${net_pnl:.2f} -> Compound (60%): ${to_compound:.2f} | Vault (40%): ${to_save:.2f}")
        elif net_pnl < 0:
            loss = abs(net_pnl)
            self.current_capital -= loss
            print(f" [-] Loss: -${loss:.2f} deducted from active capital.")
            
        self.working_capital = self.current_capital

    def get_status(self) -> Dict[str, float]:
        """گزارش دیکشنری جامع وضعیت سرمایه"""
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "working_capital": self.current_capital,
            "profit_reserve": self.profit_reserve,
            "vault_balance": self.vault_balance,
            "total_value": self.get_total_capital(),
        }
