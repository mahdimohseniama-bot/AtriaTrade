import uuid

class Order:
    def __init__(self, order_id=None, symbol=None, side=None, order_type="MARKET", quantity=0.0, price=0.0, **kwargs):
        self.order_id = order_id or f"ord_{uuid.uuid4().hex[:8]}"
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = float(quantity) if quantity is not None else 0.0
        self.price = float(price) if price is not None else 0.0

class TradingEngine:
    def __init__(self, portfolio=None, risk=None, executor=None, reserve=None, portfolio_manager=None, order_executor=None, profit_reserve=None, **kwargs):
        self.portfolio = portfolio or portfolio_manager
        self.portfolio_manager = self.portfolio
        self.risk = risk
        self.executor = executor or order_executor
        self.order_executor = self.executor
        self.reserve = reserve or profit_reserve
        self.profit_reserve = self.reserve
        self.is_running = False
        self.trades_history = []
        self._entry_prices = {}

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def _extract_tick(self, *args, **kwargs):
        tick = args[0] if args else kwargs
        if isinstance(tick, dict):
            symbol = str(tick.get("symbol", "BTCUSDT")).upper()
            price = float(tick.get("price", tick.get("current_price", 0.0)) or 0.0)
            signal = str(tick.get("signal", "HOLD")).upper()
        else:
            symbol = "BTCUSDT"
            price = 0.0
            signal = "HOLD"
        return price, signal, symbol

    def _get_balance(self, asset="USDT"):
        pm = self.portfolio
        if not pm:
            return 0.0
        if hasattr(pm, "get_balance"):
            return float(pm.get_balance(asset) or 0.0)
        if hasattr(pm, "balance"):
            return float(pm.balance or 0.0)
        return 0.0

    def _get_pos_qty(self, symbol="BTCUSDT"):
        pm = self.portfolio
        if not pm:
            return 0.0
        if hasattr(pm, "get_position"):
            pos = pm.get_position(symbol)
            if isinstance(pos, dict):
                return float(pos.get("quantity", pos.get("qty", pos.get("amount", 0.0))) or 0.0)
            if hasattr(pos, "quantity"):
                return float(pos.quantity or 0.0)
            if isinstance(pos, (int, float)):
                return float(pos)
        if hasattr(pm, "positions") and isinstance(pm.positions, dict):
            pos = pm.positions.get(symbol, 0.0)
            if isinstance(pos, dict):
                return float(pos.get("quantity", pos.get("qty", 0.0)) or 0.0)
            if hasattr(pos, "quantity"):
                return float(pos.quantity or 0.0)
            if isinstance(pos, (int, float)):
                return float(pos)
        return 0.0

    def _execute_order(self, order):
        trade_result = {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price": order.price,
            "status": "FILLED"
        }

        if self.executor:
            if hasattr(self.executor, "execute_order"):
                try:
                    res = self.executor.execute_order(order)
                    if res:
                        if isinstance(res, dict):
                            trade_result.update(res)
                        elif hasattr(res, "__dict__"):
                            trade_result.update(res.__dict__)
                except Exception:
                    pass
            elif hasattr(self.executor, "place_order"):
                try:
                    res = self.executor.place_order(order)
                    if res:
                        if isinstance(res, dict):
                            trade_result.update(res)
                        elif hasattr(res, "__dict__"):
                            trade_result.update(res.__dict__)
                except Exception:
                    pass

        if order.side == "BUY":
            self._entry_prices[order.symbol] = order.price
            if self.portfolio and hasattr(self.portfolio, "record_buy"):
                self.portfolio.record_buy(order.symbol, order.quantity, order.price)
        elif order.side == "SELL":
            entry_price = self._entry_prices.pop(order.symbol, order.price)
            profit = (order.price - entry_price) * order.quantity
            trade_result["profit"] = profit

            if profit > 0 and self.reserve:
                if hasattr(self.reserve, "add_profit"):
                    self.reserve.add_profit(profit)
                elif hasattr(self.reserve, "deposit_profit"):
                    self.reserve.deposit_profit(profit)
                elif hasattr(self.reserve, "add_to_vault"):
                    self.reserve.add_to_vault(profit)
                elif hasattr(self.reserve, "vault_balance"):
                    self.reserve.vault_balance += profit

            if self.portfolio and hasattr(self.portfolio, "record_sell"):
                self.portfolio.record_sell(order.symbol, order.quantity, order.price)

        return trade_result

    def process_tick(self, *args, **kwargs):
        if not self.is_running:
            return None

        price, signal, symbol = self._extract_tick(*args, **kwargs)
        if price <= 0 or signal not in ("BUY", "SELL"):
            return None

        pos_qty = self._get_pos_qty(symbol)

        if signal == "BUY":
            if pos_qty > 0:
                return None
            balance = self._get_balance("USDT")
            trade_amount = balance * 0.95 if balance > 0 else 100.0
            quantity = trade_amount / price
            order = Order(
                order_id=f"ord_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity,
                price=price
            )
            res = self._execute_order(order)
            self.trades_history.append(res)
            return res

        elif signal == "SELL":
            quantity = pos_qty if pos_qty > 0 else 0.01
            order = Order(
                order_id=f"ord_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=quantity,
                price=price
            )
            res = self._execute_order(order)
            self.trades_history.append(res)
            return res

        return None
