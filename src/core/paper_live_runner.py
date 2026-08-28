"""Paper Trading Live Runner module for AtriaTrade (Pure Python).

Connects market data ingestion, regime detection, signal generation,
risk management, and simulated order execution into an end-to-end loop.
"""

from typing import Dict, Any, List, Optional
from src.core.market_regime import MarketRegimeFilter, MarketRegime
from src.core.portfolio_risk import PortfolioRiskManager


class PaperTradingLiveRunner:
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        initial_balance: float = 10000.0,
        regime_filter: Optional[MarketRegimeFilter] = None,
        portfolio_risk: Optional[PortfolioRiskManager] = None
    ):
        self.symbol = symbol
        self.balance = float(initial_balance)
        self.regime_filter = regime_filter or MarketRegimeFilter(fast_window=5, slow_window=15)
        self.portfolio_risk = portfolio_risk or PortfolioRiskManager(max_total_exposure_pct=0.5)
        
        self.candles: List[Dict[str, Any]] = []
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.is_running: bool = False

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def ingest_candle(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """Ingests a new candle, detects regime, and checks trade conditions."""
        if not self.is_running:
            return {"status": "STOPPED", "reason": "Runner is not active"}

        self.candles.append(candle)
        current_price = float(candle.get("close", 0.0))

        regime_info = self.regime_filter.detect_regime(self.candles)
        current_regime = regime_info.get("regime", MarketRegime.UNKNOWN)

        return {
            "status": "PROCESSED",
            "symbol": self.symbol,
            "current_price": current_price,
            "regime": current_regime,
            "open_positions_count": len(self.open_positions),
            "balance": self.balance
        }

    def _check_risk(self, proposed_size: float) -> bool:
        """Evaluates exposure risk safely with PortfolioRiskManager."""
        current_positions_list = list(self.open_positions.values())
        proposed_pos = {
            "symbol": self.symbol,
            "size": proposed_size,
            "side": "BUY"
        }
        
        if self.portfolio_risk is not None:
            if hasattr(self.portfolio_risk, "validate_new_position"):
                try:
                    return bool(self.portfolio_risk.validate_new_position(current_positions_list, proposed_pos))
                except TypeError:
                    try:
                        return bool(self.portfolio_risk.validate_new_position(current_positions_list, proposed_pos, self.balance))
                    except Exception:
                        pass

            if hasattr(self.portfolio_risk, "evaluate_risk"):
                try:
                    res = self.portfolio_risk.evaluate_risk(current_positions_list, proposed_pos)
                    return res.get("allowed", True) if isinstance(res, dict) else bool(res)
                except Exception:
                    pass

        total_current = sum(p.get("size", 0.0) for p in current_positions_list)
        max_allowed = self.balance * getattr(self.portfolio_risk, "max_total_exposure_pct", 0.5)
        return (total_current + proposed_size) <= max_allowed

    def process_signal(self, signal: Dict[str, Any], candle: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a trading signal through regime filter, risk manager, and simulated execution."""
        if not self.is_running:
            return {"status": "REJECTED", "reason": "Runner is stopped"}

        side = signal.get("side", "").upper()
        size_pct = float(signal.get("size_pct", 0.1))
        price = float(candle.get("close", 0.0))

        if price <= 0:
            return {"status": "REJECTED", "reason": "Invalid price"}

        # الف) اگر سیگنال SELL باشد و پوزیشن باز داشته باشیم -> اقدام به بستن پوزیشن (Exit Position)
        # خروج از معامله وابسته به اجازه رژیم ورود نیست و باید انجام شود
        if side == "SELL" and self.open_positions:
            pos_id, pos = self.open_positions.popitem()
            pnl = (price - pos["entry_price"]) * pos["units"]
            return_amount = pos["size"] + pnl
            self.balance += return_amount
            close_res = {
                "status": "CLOSED",
                "position_id": pos_id,
                "side": "SELL",
                "exit_price": price,
                "pnl": round(pnl, 2),
                "remaining_balance": round(self.balance, 2)
            }
            self.trade_history.append(close_res)
            return close_res

        # ب) فیلتر رژیم بازار برای ورود به معاملات جدید (Entry)
        regime_info = self.regime_filter.detect_regime(self.candles)
        regime = regime_info.get("regime", MarketRegime.UNKNOWN)

        if not self.regime_filter.should_allow_signal(regime, side):
            return {
                "status": "REJECTED",
                "reason": f"Signal {side} not allowed in regime {regime}"
            }

        # ج) ورود به معامله خرید جدید (BUY Entry)
        trade_amount = self.balance * size_pct
        if side == "BUY":
            if not self._check_risk(trade_amount):
                return {
                    "status": "REJECTED",
                    "reason": "Risk limit exceeded"
                }

            if self.balance >= trade_amount:
                self.balance -= trade_amount
                pos_id = f"{self.symbol}_{len(self.trade_history) + 1}"
                self.open_positions[pos_id] = {
                    "id": pos_id,
                    "symbol": self.symbol,
                    "side": "BUY",
                    "entry_price": price,
                    "size": trade_amount,
                    "units": trade_amount / price
                }
                order_res = {
                    "status": "FILLED",
                    "position_id": pos_id,
                    "side": "BUY",
                    "price": price,
                    "amount": trade_amount
                }
                self.trade_history.append(order_res)
                return order_res

        return {"status": "REJECTED", "reason": "No actionable condition met"}
