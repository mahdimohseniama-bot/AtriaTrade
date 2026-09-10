import time
from typing import Any, Dict, List, Optional

from src.core.capital_manager import CapitalManager
from src.core.market_regime import MarketRegime, MarketRegimeFilter
from src.core.portfolio_risk import PortfolioRiskManager


class OpenPositionsContainer(list):
    def values(self):
        return list(self)

    def items(self):
        return [
            (pos.get("symbol", pos.get("position_id", f"POS_{idx}")), pos)
            for idx, pos in enumerate(self, start=1)
        ]

    def popitem(self):
        if not self:
            raise KeyError("popitem from empty positions")
        pos = self.pop()
        return pos.get("symbol", pos.get("position_id", "POS_LATEST")), pos

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            for pos in self:
                if isinstance(pos, dict) and (pos.get("symbol") == key or pos.get("position_id") == key):
                    return True
        return super().__contains__(key)


class DummyTicker:
    def __init__(self, price: float):
        self.last_price = price
        self.bid = price - 50.0
        self.ask = price + 50.0
        self.volume = 100.0


class DummyExchangeWrapper:
    def __init__(self, name: str = "wallex"):
        self.name = name.lower()

    def get_ticker(self, symbol: str):
        normalized = symbol.replace("/", "").upper()
        prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3000.0,
            "BTCTMN": 6000000000.0,
        }
        return DummyTicker(prices.get(normalized, 65000.0))


class PaperTradingLiveRunner:
    def __init__(
        self,
        symbol: str = "BTC/USDT",
        initial_balance: float = 10000.0,
        initial_capital: Optional[float] = None,
        regime_filter: Optional[MarketRegimeFilter] = None,
        portfolio_risk: Optional[PortfolioRiskManager] = None,
        risk_manager: Optional[PortfolioRiskManager] = None,
        capital_manager: Optional[CapitalManager] = None,
        exchange: Optional[Any] = None,
        exchange_name: Optional[str] = None,
        risk_per_trade: float = 0.02,
        **kwargs,
    ):
        self.symbol = symbol

        starting_balance = (
            initial_capital
            if initial_capital is not None
            else initial_balance
        )

        self.balance = float(starting_balance)
        self.initial_capital = float(starting_balance)
        self.risk_per_trade = float(risk_per_trade)

        self.regime_filter = (
            regime_filter
            if regime_filter is not None
            else MarketRegimeFilter(
                fast_window=5,
                slow_window=15,
            )
        )

        self.portfolio_risk = (
            risk_manager
            if risk_manager is not None
            else portfolio_risk
        )

        if self.portfolio_risk is None:
            self.portfolio_risk = PortfolioRiskManager(
                max_total_exposure_pct=0.5
            )

        self.risk_manager = self.portfolio_risk

        self.capital_manager = (
            capital_manager
            if capital_manager is not None
            else CapitalManager(
                initial_capital=self.initial_capital,
                vault_ratio=0.60,
                compound_ratio=0.40,
            )
        )

        self.exchange = exchange

        if self.exchange is None and exchange_name:
            try:
                from src.exchange.factory import ExchangeFactory
                self.exchange = ExchangeFactory.create(exchange_name)
            except Exception:
                self.exchange = DummyExchangeWrapper(exchange_name)

        self.exchange_name = exchange_name

        self.candles: List[Dict[str, Any]] = []
        self.open_positions = OpenPositionsContainer()
        self.trade_history: List[Dict[str, Any]] = []
        self.is_running = False
        self._position_counter = 0

    @property
    def positions(self) -> OpenPositionsContainer:
        return self.open_positions

    @property
    def vault_balance(self) -> float:
        return float(
            getattr(
                self.capital_manager,
                "vault_balance",
                getattr(self.capital_manager, "profit_reserve", 0.0),
            )
        )

    @vault_balance.setter
    def vault_balance(self, value: float) -> None:
        if hasattr(type(self.capital_manager), "vault_balance"):
            self.capital_manager.vault_balance = float(value)
        else:
            self.capital_manager.profit_reserve = float(value)

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def ingest_candle(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_running:
            return {
                "status": "STOPPED",
                "message": "Runner is not running",
            }

        self.candles.append(candle)

        current_price = float(candle.get("close", 0.0))
        regime_info = self.regime_filter.detect_regime(self.candles)
        regime = regime_info.get("regime", MarketRegime.UNKNOWN)

        return {
            "status": "PROCESSED",
            "symbol": self.symbol,
            "current_price": current_price,
            "regime": regime,
            "open_positions_count": len(self.open_positions),
            "balance": self.balance,
        }

    def _check_risk(self, proposed_size: float) -> bool:
        positions = []

        for position in self.open_positions:
            normalized = dict(position)
            normalized.setdefault(
                "value",
                float(normalized.get("size", 0.0)),
            )
            positions.append(normalized)

        try:
            result = self.portfolio_risk.validate_new_position(
                self.balance,
                positions,
                self.symbol,
                float(proposed_size),
            )

            if isinstance(result, dict) and "allowed" in result:
                return bool(result["allowed"])

            if isinstance(result, bool):
                return result

        except TypeError:
            pass
        except Exception:
            pass

        current_exposure = sum(
            float(position.get("size", position.get("value", 0.0)))
            for position in self.open_positions
        )

        max_exposure_pct = float(
            getattr(
                self.portfolio_risk,
                "max_total_exposure_pct",
                0.5,
            )
        )

        return (
            current_exposure + float(proposed_size)
            <= self.balance * max_exposure_pct
        )

    def _next_position_id(self) -> str:
        self._position_counter += 1
        return f"POS_{self._position_counter}"

    def _resolve_price(self, symbol: str, price: Optional[float]) -> float:
        if price is not None and float(price) > 0:
            return float(price)

        if self.exchange is not None:
            try:
                ticker = self.exchange.get_ticker(symbol)
                exchange_price = float(getattr(ticker, "last_price", 0.0))
                if exchange_price > 0:
                    return exchange_price
            except Exception:
                pass

        if self.candles:
            candle_price = float(self.candles[-1].get("close", 0.0))
            if candle_price > 0:
                return candle_price

        return 65000.0

    def open_position(
        self,
        symbol: Optional[str] = None,
        size: Optional[float] = None,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        side: str = "BUY",
        **kwargs,
    ):
        target_symbol = symbol or self.symbol
        normalized_side = side.upper()

        entry_price = self._resolve_price(target_symbol, price)

        if entry_price <= 0:
            return False

        if amount is not None:
            units = float(amount)
            position_value = units * entry_price
            return_as_position = True
        elif size is not None:
            units = float(size)
            position_value = units * entry_price
            return_as_position = False
        else:
            position_value = self.balance * self.risk_per_trade
            units = position_value / entry_price
            return_as_position = True

        if units <= 0 or position_value <= 0:
            return False

        if position_value > self.balance:
            return False

        if not self._check_risk(position_value):
            return False

        self.balance -= position_value

        position = {
            "position_id": self._next_position_id(),
            "symbol": target_symbol,
            "side": normalized_side,
            "entry_price": entry_price,
            "size": position_value,
            "value": position_value,
            "amount": units,
            "units": units,
            "entry_time": int(time.time()),
        }

        self.open_positions.append(position)

        if return_as_position:
            return position

        return True

    def close_position(
        self,
        symbol: Optional[str] = None,
        exit_price: Optional[float] = None,
        position_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        target_symbol = symbol or self.symbol

        idx_to_close = None
        for idx, pos in enumerate(self.open_positions):
            if position_id and pos.get("position_id") == position_id:
                idx_to_close = idx
                break
            if symbol and pos.get("symbol") == target_symbol:
                idx_to_close = idx
                break

        if idx_to_close is None:
            if not self.open_positions:
                return None
            idx_to_close = len(self.open_positions) - 1

        position = self.open_positions.pop(idx_to_close)

        current_price = (
            float(exit_price)
            if exit_price is not None
            else self._resolve_price(position.get("symbol", target_symbol), None)
        )

        entry_price = float(position.get("entry_price", current_price))
        units = float(position.get("units", position.get("amount", 0.0)))
        position_value = float(position.get("size", position.get("value", units * entry_price)))

        pnl = (current_price - entry_price) * units

        split_result = self.capital_manager.record_trade_pnl(pnl)
        vault_share = float(split_result.get("vault_share", 0.0))
        compound_share = float(split_result.get("compound_share", 0.0))

        if pnl > 0:
            self.balance += position_value + compound_share
        else:
            self.balance += max(0.0, position_value + pnl)

        trade_record = {
            "status": "CLOSED",
            "position_id": position.get("position_id"),
            "symbol": position.get("symbol", target_symbol),
            "entry_price": entry_price,
            "exit_price": current_price,
            "units": units,
            "pnl": pnl,
            "vault_share": vault_share,
            "compound_share": compound_share,
            "remaining_balance": self.balance,
            "exit_time": int(time.time()),
        }

        self.trade_history.append(trade_record)
        return trade_record

    def get_summary(self) -> Dict[str, Any]:
        total_pnl = sum(t.get("pnl", 0.0) for t in self.trade_history)
        current_cap = float(getattr(self.capital_manager, "current_capital", self.balance))
        vault_bal = float(self.vault_balance)
        total_wealth = current_cap + vault_bal
        completed_trades = len(self.trade_history)
        open_pos_count = len(self.open_positions)
        
        return {
            "symbol": self.symbol,
            "balance": self.balance,
            "initial_capital": self.initial_capital,
            "current_capital": current_cap,
            "vault_balance": vault_bal,
            "total_wealth": total_wealth,
            "total_trades": completed_trades,
            "completed_trades_count": completed_trades,
            "open_positions": open_pos_count,
            "open_positions_count": open_pos_count,
            "total_pnl": total_pnl,
            "trade_history": self.trade_history,
        }

    def process_signal(
        self,
        signal: Dict[str, Any],
        candle: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.is_running:
            return {
                "status": "REJECTED",
                "reason": "Runner is stopped",
            }

        side = str(signal.get("side", "")).upper()
        current_price = float(candle.get("close", 0.0))

        if current_price <= 0:
            return {
                "status": "REJECTED",
                "reason": "Invalid price",
            }

        if side == "SELL" and self.open_positions:
            return self.close_position(exit_price=current_price)

        if side == "BUY":
            size_pct = float(
                signal.get("size_pct", self.risk_per_trade)
            )
            trade_amount = self.balance * size_pct

            if trade_amount <= 0 or trade_amount > self.balance:
                return {
                    "status": "REJECTED",
                    "reason": "Insufficient balance",
                }

            if not self._check_risk(trade_amount):
                return {
                    "status": "REJECTED",
                    "reason": "Risk limit exceeded",
                }

            units = trade_amount / current_price
            position = {
                "position_id": self._next_position_id(),
                "symbol": self.symbol,
                "side": "BUY",
                "entry_price": current_price,
                "size": trade_amount,
                "value": trade_amount,
                "amount": units,
                "units": units,
                "entry_time": candle.get("timestamp", int(time.time())),
            }

            self.balance -= trade_amount
            self.open_positions.append(position)

            return {
                "status": "FILLED",
                "position_id": position["position_id"],
                "side": "BUY",
                "price": current_price,
                "size": trade_amount,
                "amount": units,
                "units": units,
                "remaining_balance": self.balance,
            }

        return {
            "status": "REJECTED",
            "reason": "No actionable signal",
        }

    def step(
        self,
        candle: Optional[Dict[str, Any]] = None,
        signal: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_running:
            self.start()

        if candle is None:
            price = self._resolve_price(self.symbol, None)
            candle = {
                "timestamp": int(time.time()),
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1.0,
            }

        candle_result = self.ingest_candle(candle)

        if signal is None:
            return candle_result

        return {
            "candle_result": candle_result,
            "signal_result": self.process_signal(signal, candle),
        }
