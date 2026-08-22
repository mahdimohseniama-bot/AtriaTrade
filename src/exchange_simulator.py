import random
import time

class ExchangeSimulator:
    def __init__(self, initial_price=60000.0):
        self.current_price = initial_price
        self.positions = {}

    def get_market_price(self, symbol="BTCUSDT"):
        # شبیه‌سازی نوسان قیمت تصادفی بین -0.5% تا +0.5%
        fluctuation = random.uniform(-0.005, 0.005)
        self.current_price *= (1 + fluctuation)
        return round(self.current_price, 2)

    def execute_order(self, symbol, order_type, amount, side):
        price = self.get_market_price(symbol)
        order_id = random.randint(10000, 99999)
        print(f"[EXSIM] Order Executed: {side.upper()} {amount} {symbol} at ${price} (ID: {order_id})")
        return {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "status": "FILLED"
        }

if __name__ == "__main__":
    ex = ExchangeSimulator()
    print("Testing Exchange Simulator...")
    for i in range(3):
        p = ex.get_market_price("BTCUSDT")
        print(f"Tick {i+1} - BTC Price: ${p}")
    
    ex.execute_order("BTCUSDT", "MARKET", 0.01, "buy")
