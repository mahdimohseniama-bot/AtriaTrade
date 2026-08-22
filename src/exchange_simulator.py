import random
from typing import Dict, Any

class ExchangeSimulator:
    def __init__(self, initial_usdt: float = 1000.0, taker_fee: float = 0.001, slippage: float = 0.0005):
        self.wallets: Dict[str, float] = {
            "USDT": initial_usdt,
            "BTC": 0.0
        }
        self.taker_fee = taker_fee
        self.slippage = slippage

    def get_market_price(self, symbol: str) -> float:
        """قیمت پایه بازار (BTC)"""
        return 60000.0

    def execute_order(self, symbol: str, side: str, amount: float, price: float = None) -> Dict[str, Any]:
        """اجرای سفارش شبیه‌سازی شده با اعمال کارمزد و اسلیپیج"""
        base_price = price if price is not None else self.get_market_price(symbol)
        
        # اعمال لغزش قیمت (Slippage)
        if side.upper() == "BUY":
            exec_price = base_price * (1 + self.slippage)
        else:
            exec_price = base_price * (1 - self.slippage)

        cost = amount * exec_price
        fee = cost * self.taker_fee

        if side.upper() == "BUY":
            total_cost = cost + fee
            if self.wallets["USDT"] < total_cost:
                return {"status": "REJECTED", "reason": "Insufficient USDT balance"}
            self.wallets["USDT"] -= total_cost
            self.wallets["BTC"] += amount
        elif side.upper() == "SELL":
            if self.wallets["BTC"] < amount:
                return {"status": "REJECTED", "reason": "Insufficient BTC balance"}
            self.wallets["BTC"] -= amount
            net_return = cost - fee
            self.wallets["USDT"] += net_return
        else:
            return {"status": "REJECTED", "reason": "Invalid side"}

        return {
            "status": "FILLED",
            "symbol": symbol,
            "side": side.upper(),
            "amount": amount,
            "price": exec_price,
            "fee": fee,
            "cost": cost
        }

    def get_balances(self) -> Dict[str, float]:
        return self.wallets.copy()
