from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class TradeHistory:
    """
    ذخیره امن و دائمی تاریخچه معاملات Paper Trading.
    فایل پیش‌فرض: data/trade_history.json
    """

    def __init__(self, file_path: str = "data/trade_history.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self._atomic_write([])

    def _atomic_write(self, data: List[Dict[str, Any]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Optional[Path] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.file_path.parent,
                prefix=".trade_history_",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                json.dump(data, temp_file, ensure_ascii=False, indent=2)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_path = Path(temp_file.name)

            os.replace(temp_path, self.file_path)

        except Exception:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise

    def _read(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("trade_history.json root must be a list")

            return data

        except json.JSONDecodeError:
            backup_path = self.file_path.with_suffix(".corrupted.json")
            self.file_path.replace(backup_path)
            print(f"[WARNING] Trade history was corrupted and moved to {backup_path}")
            return []

    def add_trade(
        self,
        symbol: str,
        side: str,
        amount: float,
        execution_price: float,
        fee: float,
        net_pnl: Optional[float],
        capital_status: Dict[str, float],
    ) -> Dict[str, Any]:
        side = str(side).upper()

        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if execution_price <= 0:
            raise ValueError("execution_price must be > 0")

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": str(symbol),
            "side": side,
            "amount": round(float(amount), 12),
            "execution_price": round(float(execution_price), 8),
            "fee": round(float(fee), 8),
            "net_pnl": None if net_pnl is None else round(float(net_pnl), 8),
            "capital_status": {
                "initial_capital": round(float(capital_status.get("initial_capital", 0.0)), 8),
                "current_capital": round(float(capital_status.get("current_capital", 0.0)), 8),
                "profit_reserve": round(float(capital_status.get("profit_reserve", 0.0)), 8),
                "total_value": round(float(capital_status.get("total_value", 0.0)), 8),
            },
        }

        history = self._read()
        history.append(record)
        self._atomic_write(history)
        return record

    def get_all(self) -> List[Dict[str, Any]]:
        return self._read()

    def count(self) -> int:
        return len(self._read())

    def clear(self) -> None:
        self._atomic_write([])
