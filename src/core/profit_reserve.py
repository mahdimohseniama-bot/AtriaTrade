import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

class ProfitReserveManager:
    """
    مدیریت سود حاصل از معاملات و تفکیک آن از اصل سرمایه (Capital Protection).
    """
    def __init__(self, reserve_ratio: float = 0.5):
        """
        :param reserve_ratio: درصد سودی که باید ذخیره شود (پیش‌فرض ۵۰ درصد)
        """
        if not (0.0 <= reserve_ratio <= 1.0):
            raise ValueError("Reserve ratio must be between 0.0 and 1.0")
            
        self.reserve_ratio = reserve_ratio
        self.total_profit_locked = 0.0
        self.reserve_vault = 0.0
        self.active_capital_added = 0.0

    def process_trade_pnl(self, pnl: float) -> dict:
        """
        بررسی نتیجه معامله بسته شده:
        - اگر سود بود: تفکیک درصد مشخص به صندوق ذخیره و مابقی به سرمایه در گردش.
        - اگر ضرر بود: ثبت در لاگ بدون کسر از صندوق ذخیره.
        """
        if pnl > 0:
            reserve_amount = pnl * self.reserve_ratio
            reinvest_amount = pnl - reserve_amount
            
            self.reserve_vault += reserve_amount
            self.active_capital_added += reinvest_amount
            self.total_profit_locked += pnl
            
            logging.info(f"💰 Profit Locked: +${pnl:.2f} | Vault: +${reserve_amount:.2f} | Reinvest: +${reinvest_amount:.2f}")
            return {
                "status": "PROFIT",
                "pnl": pnl,
                "vault_added": reserve_amount,
                "reinvest_added": reinvest_amount,
                "total_vault": self.reserve_vault
            }
        else:
            logging.info(f"🔻 Loss Recorded: -${abs(pnl):.2f} (Vault protected: ${self.reserve_vault:.2f})")
            return {
                "status": "LOSS",
                "pnl": pnl,
                "vault_added": 0.0,
                "reinvest_added": 0.0,
                "total_vault": self.reserve_vault
            }

    def get_reserve_summary(self) -> dict:
        return {
            "reserve_ratio": self.reserve_ratio,
            "total_profit_locked": round(self.total_profit_locked, 4),
            "reserve_vault": round(self.reserve_vault, 4),
            "active_capital_added": round(self.active_capital_added, 4)
        }
