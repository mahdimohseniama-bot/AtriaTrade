import random
import time
from datetime import datetime

class ExchangeSimulator:
    def __init__(self, initial_usdt=100.0, maker_fee=0.001, taker_fee=0.001):
        # کیف پول مجازی صرافی
        self.balances = {
            "USDT": float(initial_usdt),
            "BTC": 0.0
        }
        self.current_price = 60000.0
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.trade_history = []

    def get_market_price(self, symbol="BTCUSDT"):
        # شبیه‌سازی نوسان قیمت تصادفی بین -0.5% تا +0.5%
        fluctuation = random.uniform(-0.005, 0.005)
        self.current_price = round(self.current_price * (1 + fluctuation), 2)
        return self.current_price

    def get_balance(self, asset="USDT"):
        return self.balances.get(asset, 0.0)

    def execute_order(self, symbol, order_type, amount, side):
        market_price = self.get_market_price(symbol)
        
        # شبیه‌سازی لغزش قیمت (Slippage): در خرید کمی گران‌تر، در فروش کمی ارزان‌تر
        slippage_rate = random.uniform(0.0001, 0.0005)
        if side.lower() == "buy":
            exec_price = round(market_price * (1 + slippage_rate), 2)
            total_cost = exec_price * amount
            fee = round(total_cost * self.taker_fee, 4)
            required_usdt = total_cost + fee

            if self.balances["USDT"] < required_usdt:
                print(f"[!] Order Rejected: Insufficient USDT. Need ${required_usdt:.2f}, Have ${self.balances['USDT']:.2f}")
                return None

            # کسر تتر و واریز بیت‌کوین
            self.balances["USDT"] -= required_usdt
            self.balances["BTC"] += amount

        elif side.lower() == "sell":
            exec_price = round(market_price * (1 - slippage_rate), 2)
            if self.balances["BTC"] < amount:
                print(f"[!] Order Rejected: Insufficient BTC. Need {amount} BTC, Have {self.balances['BTC']} BTC")
                return None

            gross_usdt = exec_price * amount
            fee = round(gross_usdt * self.taker_fee, 4)
            net_usdt = gross_usdt - fee

            # کسر بیت‌کوین و واریز تتر
            self.balances["BTC"] -= amount
            self.balances["USDT"] += net_usdt
        else:
            print(f"[!] Invalid side: {side}")
            return None

        order_id = random.randint(100000, 999999)
        trade_record = {
            "order_id": order_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "side": side.upper(),
            "amount": amount,
            "price": exec_price,
            "fee": fee,
            "status": "FILLED"
        }
        self.trade_history.append(trade_record)
        
        print(f"[EXSIM] {side.upper()} {amount} {symbol} @ ${exec_price:.2f} | Fee: ${fee:.4f} | Wallet: USDT: ${self.balances['USDT']:.2f}, BTC: {self.balances['BTC']:.4f}")
        return trade_record

if __name__ == "__main__":
    ex = ExchangeSimulator(initial_usdt=100.0)
    print("Initial Wallet State:", ex.balances)
    
    # تست خرید مجازی
    print("\n--- Testing Buy ---")
    ex.execute_order("BTCUSDT", "MARKET", amount=0.001, side="buy")
    
    # تست فروش مجازی
    print("\n--- Testing Sell ---")
    ex.execute_order("BTCUSDT", "MARKET", amount=0.001, side="sell")
