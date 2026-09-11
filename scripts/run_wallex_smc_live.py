#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AtriaTrade - Wallex SMC Live Runner (Paper Trading Mode)
سازگار با محیط Termux و مدل مالی 60/40
"""

import sys
import os
import time
import inspect
import logging
from typing import Dict, Any

# اطمینان از قرار داشتن ریشه پروژه در PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.adapters.wallex_paper import WallexPaperAdapter
except ImportError:
    try:
        from src.adapters.wallex_adapter import WallexAdapter as WallexPaperAdapter
    except ImportError:
        WallexPaperAdapter = None

from src.core.profit_reserve import ProfitReserveManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AtriaTrade-Runner")


class WallexSMCLiveRunner:
    """رانر اختصاصی اجرای استراتژی SMC در شبیه‌ساز والکس."""

    def __init__(self, symbol: str = "BTCUSDT", initial_capital: float = 100.0, reserve_ratio: float = 0.6):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.reserve_ratio = reserve_ratio

        # ۱. راه‌اندازی داینامیک آداپتور والکس
        self.adapter = self._init_adapter(initial_capital)

        # ۲. راه‌اندازی ماژول ذخیره سود (مدل ۶۰٪ برداشت به خزانه / ۴۰٪ کامپاند)
        self.reserve_manager = ProfitReserveManager(reserve_ratio=self.reserve_ratio)

        self.running = False
        self.iteration = 0

    def _init_adapter(self, initial_capital: float):
        """مقداردهی امن آداپتور والکس بر اساس امضای سازنده."""
        if WallexPaperAdapter is None:
            logger.warning("آداپتور والکس یافت نشد؛ در حالت Mock اجرا می‌شود.")
            return None

        sig = inspect.signature(WallexPaperAdapter.__init__)
        params = sig.parameters

        kwargs: Dict[str, Any] = {}
        if "initial_balance_usdt" in params:
            kwargs["initial_balance_usdt"] = initial_capital
        elif "initial_balances" in params:
            kwargs["initial_balances"] = {"USDT": initial_capital, "TMN": 0.0}
        elif "initial_balance" in params:
            kwargs["initial_balance"] = initial_capital

        try:
            adapter = WallexPaperAdapter(**kwargs)
            logger.info("آداپتور والکس با موفقیت لود شد.")
            return adapter
        except Exception as e:
            logger.error(f"خطا در ایجاد WallexPaperAdapter: {e}")
            return None

    def get_vault_balance(self) -> float:
        """استخراج امن موجودی خزانه سود بدون ریسک AttributeError."""
        if hasattr(self.reserve_manager, "get_vault_balance") and callable(self.reserve_manager.get_vault_balance):
            try:
                return float(self.reserve_manager.get_vault_balance())
            except Exception:
                pass

        if hasattr(self.reserve_manager, "vault_balance"):
            return float(self.reserve_manager.vault_balance)

        if hasattr(self.reserve_manager, "total_reserved_profit"):
            return float(self.reserve_manager.total_reserved_profit)

        return 0.0

    def get_current_balance(self) -> float:
        """استخراج موجودی جاری ترید."""
        if self.adapter is None:
            return self.initial_capital

        if hasattr(self.adapter, "get_balance"):
            try:
                bal = self.adapter.get_balance("USDT")
                if isinstance(bal, dict):
                    return float(bal.get("free", bal.get("total", self.initial_capital)))
                return float(bal)
            except Exception:
                pass

        if hasattr(self.adapter, "balances") and isinstance(self.adapter.balances, dict):
            return float(self.adapter.balances.get("USDT", self.initial_capital))

        return self.initial_capital

    def display_status(self):
        """نمایش ساختاریافته وضعیت ربات در CLI."""
        current_bal = self.get_current_balance()
        vault_bal = self.get_vault_balance()
        total_equity = current_bal + vault_bal
        pnl = total_equity - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0.0

        print("\n" + "=" * 55)
        print("          🚀 ATRIA-TRADE WALLEX SMC RUNNER 🚀          ")
        print("=" * 55)
        print(f"🔹 نماد معاملاتی:          {self.symbol}")
        print(f"🔹 دور اجرای حلقه:         #{self.iteration}")
        print(f"💵 سرمایه اولیه:           ${self.initial_capital:.2f}")
        print(f"📊 موجودی ترید فعال:       ${current_bal:.2f}")
        print(f"🔒 خزانه سود قابل‌برداشت:   ${vault_bal:.2f} ({int(self.reserve_ratio * 100)}%)")
        print(f"📈 مجموع دارایی (Equity):  ${total_equity:.2f}")
        print(f"🎯 سود/زیان کل (PnL):      {pnl:+.2f} USDT ({pnl_pct:+.2f}%)")
        print("=" * 55 + "\n")

    def run_loop(self, poll_interval: int = 5):
        """حلقه اصلی اجرای استراتژی در ترمینال."""
        self.running = True
        logger.info(f"شروع اجرای زنده روی {self.symbol} با وقفه {poll_interval} ثانیه...")

        try:
            while self.running:
                self.iteration += 1
                self.display_status()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("توقف دستی توسط کاربر (Ctrl+C). خروج ایمن.")
        finally:
            self.running = False


if __name__ == "__main__":
    runner = WallexSMCLiveRunner(symbol="BTCUSDT", initial_capital=100.0, reserve_ratio=0.6)
    runner.run_loop(poll_interval=5)
