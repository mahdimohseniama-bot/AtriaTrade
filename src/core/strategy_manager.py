import logging
from typing import Dict, List, Type
import importlib

logger = logging.getLogger(__name__)

class StrategyManager:
    """
    مدیریت و اجرای استراتژی‌های مختلف معاملاتی.
    این کلاس مسئول بارگذاری، فعال‌سازی و مدیریت چرخه حیات استراتژی‌هاست.
    """
    def __init__(self, engine):
        self.engine = engine
        self.active_strategies: Dict[str, object] = {}
        self.logger = logging.getLogger(__name__)

    def load_strategy(self, strategy_class: Type) -> str:
        """بارگذاری یک استراتژی و اضافه کردن آن به لیست مدیریت شده"""
        strategy_instance = strategy_class(self.engine)
        name = strategy_instance.name
        self.active_strategies[name] = strategy_instance
        self.logger.info(f"Strategy '{name}' loaded successfully.")
        return name

    def start_all(self):
        """شروع اجرای تمام استراتژی‌های بارگذاری شده"""
        for name, strategy in self.active_strategies.items():
            try:
                strategy.start()
                self.logger.info(f"Strategy '{name}' started.")
            except Exception as e:
                self.logger.error(f"Failed to start strategy '{name}': {e}")

    def stop_all(self):
        """توقف تمام استراتژی‌ها"""
        for name, strategy in self.active_strategies.items():
            try:
                strategy.stop()
                self.logger.info(f"Strategy '{name}' stopped.")
            except Exception as e:
                self.logger.error(f"Error stopping strategy '{name}': {e}")

    def update(self, market_data: dict):
        """
        این متد در هر تیک (Tick) توسط TradingEngine فراخوانی می‌شود.
        تمام استراتژی‌های فعال را با داده‌های جدید آپدیت می‌کند.
        """
        for name, strategy in self.active_strategies.items():
            try:
                # استراتژی داده را می‌گیرد و در صورت نیاز سیگنال تولید می‌کند
                signal = strategy.on_tick(market_data)
                if signal:
                    self.logger.info(f"Signal received from {name}: {signal}")
                    # ارسال سیگنال به موتور اصلی برای اجرا
                    self.engine.handle_strategy_signal(name, signal)
            except Exception as e:
                self.logger.error(f"Error in strategy '{name}' during update: {e}")

    def remove_strategy(self, name: str):
        """حذف یک استراتژی خاص"""
        if name in self.active_strategies:
            self.active_strategies[name].stop()
            del self.active_strategies[name]
            self.logger.info(f"Strategy '{name}' removed.")

