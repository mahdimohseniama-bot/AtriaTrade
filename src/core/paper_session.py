import json
import os
from datetime import datetime

from src.core.capital_manager import CapitalManager
from src.core.risk_manager import RiskManager, RiskConfig
from src.core.trader_engine import TraderEngine


class PaperSession:
    def __init__(self, session_name: str, initial_capital: float = 10000.0, risk_config: RiskConfig = None):
        if not session_name or not isinstance(session_name, str):
            raise ValueError("Session name must be a non-empty string.")
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")

        self.session_name = session_name
        self.initial_capital = float(initial_capital)

        self.capital_manager = CapitalManager(initial_capital=self.initial_capital)
        self.risk_manager = RiskManager(config=risk_config or RiskConfig())
        self.engine = TraderEngine(
            capital_manager=self.capital_manager,
            risk_manager=self.risk_manager
        )

        self.trades_history = []
        self.sessions_dir = "data/paper_trades"
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _get_portfolio_snapshot(self) -> dict:
        cm = self.capital_manager
        current_capital = float(getattr(cm, "current_capital", self.initial_capital))
        profit_reserve = float(getattr(cm, "profit_reserve", 0.0))
        total_value = float(getattr(cm, "total_value", current_capital + profit_reserve))

        return {
            "current_capital": current_capital,
            "profit_reserve": profit_reserve,
            "total_value": total_value,
        }

    def execute_trade(self, symbol: str, side: str, entry_price: float, exit_price: float) -> dict:
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string.")
        if side not in ["buy", "sell"]:
            raise ValueError("Side must be either 'buy' or 'sell'.")
        if entry_price <= 0 or exit_price <= 0:
            raise ValueError("Prices must be positive.")

        open_res = self.engine.open_virtual_position(
            symbol=symbol,
            side=side,
            current_price=entry_price
        )

        if isinstance(open_res, str) or getattr(open_res, "status", None) == "REJECTED":
            trade_record = {
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": 0.0,
                "status": "REJECTED",
                "timestamp": datetime.now().isoformat()
            }
            self.trades_history.append(trade_record)
            self.save_session()
            return trade_record

        close_res = self.engine.close_virtual_position(
            symbol=symbol,
            exit_price=exit_price
        )

        pnl_val = getattr(close_res, "pnl", 0.0)

        trade_record = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": float(pnl_val),
            "status": "CLOSED",
            "timestamp": datetime.now().isoformat()
        }
        self.trades_history.append(trade_record)
        self.save_session()
        return trade_record

    def get_session_stats(self) -> dict:
        closed_trades = [t for t in self.trades_history if t.get("status") == "CLOSED"]
        total_trades = len(closed_trades)
        winning_trades = len([t for t in closed_trades if float(t.get("pnl", 0.0)) > 0])
        losing_trades = len([t for t in closed_trades if float(t.get("pnl", 0.0)) < 0])
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        total_pnl = sum(float(t.get("pnl", 0.0)) for t in closed_trades)

        portfolio = self._get_portfolio_snapshot()

        return {
            "session_name": self.session_name,
            "initial_capital": self.initial_capital,
            "current_capital": portfolio["current_capital"],
            "profit_reserve": portfolio["profit_reserve"],
            "total_value": portfolio["total_value"],
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_pct": round(win_rate, 2),
            "total_pnl": round(total_pnl, 4),
        }

    def _to_json_safe(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return {k: self._to_json_safe(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, dict):
            return {k: self._to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._to_json_safe(item) for item in obj]
        return obj

    def save_session(self):
        file_path = os.path.join(self.sessions_dir, f"{self.session_name}.json")
        data = {
            "session_name": self.session_name,
            "initial_capital": self.initial_capital,
            "portfolio": self._get_portfolio_snapshot(),
            "stats": self.get_session_stats(),
            "trades_history": self._to_json_safe(self.trades_history),
            "updated_at": datetime.now().isoformat(),
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @classmethod
    def load_session(cls, session_name: str) -> "PaperSession":
        file_path = os.path.join("data/paper_trades", f"{session_name}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Session file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        initial_cap = float(data.get("initial_capital", 10000.0))
        session = cls(session_name=session_name, initial_capital=initial_cap)

        session.trades_history = data.get("trades_history", [])
        portfolio = data.get("portfolio", {})

        if "current_capital" in portfolio:
            session.capital_manager.current_capital = float(portfolio["current_capital"])
        if "profit_reserve" in portfolio:
            session.capital_manager.profit_reserve = float(portfolio["profit_reserve"])
        if "total_value" in portfolio and hasattr(session.capital_manager, "total_value"):
            session.capital_manager.total_value = float(portfolio["total_value"])

        return session
