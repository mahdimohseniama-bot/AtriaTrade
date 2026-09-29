import logging

class CapitalManager:
    def __init__(self, initial_capital: float):
        self.capital = initial_capital
        self.logger = logging.getLogger("CapitalManager")

    def record_trade_result(self, pnl: float, fee: float = 0.0):
        # Updating capital based on PnL and fees
        self.capital += (pnl - fee)
        self.logger.info(f"Trade recorded. PnL: {pnl}, Fee: {fee}. New Balance: {self.capital}")

    def get_balance(self):
        return self.capital
