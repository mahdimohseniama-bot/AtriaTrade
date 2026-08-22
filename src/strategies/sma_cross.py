class SMACrossStrategy:
    def __init__(self, short_window=5, long_window=15):
        self.short_window = short_window
        self.long_window = long_window
        self.prices = []

    def add_price(self, price: float):
        self.prices.append(price)
        # فقط به اندازه پنجره طولانی قیمت نگه می‌داریم تا رم الکی مصرف نشه
        if len(self.prices) > self.long_window + 5:
            self.prices.pop(0)

    def calculate_sma(self, window: int):
        if len(self.prices) < window:
            return None
        return sum(self.prices[-window:]) / window

    def generate_signal(self, current_price: float) -> str:
        self.add_price(current_price)
        
        # اگر هنوز دیتای کافی جمع نشده، صبر کن
        if len(self.prices) < self.long_window:
            return "HOLD"

        short_sma = self.calculate_sma(self.short_window)
        long_sma = self.calculate_sma(self.long_window)

        # اگر میانگین سریع بالاتر از میانگین کند بره = سیگنال خرید
        if short_sma > long_sma:
            return "BUY"
        # اگر میانگین سریع زیر میانگین کند بیاد = سیگنال فروش
        elif short_sma < long_sma:
            return "SELL"
        
        return "HOLD"

if __name__ == "__main__":
    strategy = SMACrossStrategy(short_window=3, long_window=5)
    test_prices = [100, 101, 102, 103, 105, 104, 102, 100, 98]
    
    print("Testing SMA Strategy...")
    for p in test_prices:
        sig = strategy.generate_signal(p)
        print(f"Price: {p} -> Signal: {sig}")
