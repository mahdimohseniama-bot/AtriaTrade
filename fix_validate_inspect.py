import sys
from pathlib import Path

path = Path("src/core/order_executor.py")
text = path.read_text(encoding="utf-8")
lines = text.split("\n")

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith("    def _validate_order("):
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("    def "):
            end_idx = i
            break
    if end_idx == -1:
        end_idx = len(lines)

if start_idx != -1:
    new_method = [
        '    def _validate_order(self, *args, **kwargs) -> None:',
        '        import inspect',
        '        order = kwargs.get("order")',
        '        if order is None and len(args) > 0:',
        '            order = args[0]',
        '            ',
        '        symbol = kwargs.get("symbol", getattr(order, "symbol", None))',
        '        side = kwargs.get("side", getattr(order, "side", None))',
        '        quantity = kwargs.get("quantity", getattr(order, "quantity", None))',
        '        price = kwargs.get("price", getattr(order, "price", 0.0))',
        '        stop_loss = kwargs.get("stop_loss", getattr(order, "stop_loss", None))',
        '        ',
        '        side_str = "BUY"',
        '        if side:',
        '            side_str = str(getattr(side, "value", side)).upper()',
        '            ',
        '        p = float(price or 0.0)',
        '        if p == 0.0 and hasattr(order, "current_price") and getattr(order, "current_price") is not None:',
        '            p = float(getattr(order, "current_price"))',
        '            ',
        '        if hasattr(self, "risk_manager") and self.risk_manager is not None:',
        '            obj_to_validate = order',
        '            if obj_to_validate is None:',
        '                class DummyOrder: pass',
        '                obj_to_validate = DummyOrder()',
        '                obj_to_validate.symbol = symbol',
        '                obj_to_validate.side = side',
        '                obj_to_validate.quantity = quantity',
        '                obj_to_validate.price = p',
        '                obj_to_validate.stop_loss = stop_loss',
        '                ',
        '            if hasattr(self.risk_manager, "validate_order"):',
        '                sig = inspect.signature(self.risk_manager.validate_order)',
        '                params = list(sig.parameters.keys())',
        '                try:',
        '                    if "price" in params and len(params) >= 2 and params[0] != "symbol":',
        '                        res = self.risk_manager.validate_order(obj_to_validate, p)',
        '                    elif "symbol" in params:',
        '                        res = self.risk_manager.validate_order(symbol=symbol, side=side, quantity=quantity, price=p)',
        '                    else:',
        '                        res = self.risk_manager.validate_order(obj_to_validate)',
        '                except TypeError as e:',
        '                    if "price" in str(e):',
        '                        res = self.risk_manager.validate_order(obj_to_validate, p)',
        '                    else:',
        '                        raise e',
        '                        ',
        '                if isinstance(res, dict) and not res.get("is_valid", True):',
        '                    raise ValueError(res.get("reason", "Order rejected by RiskManager"))',
        '                elif res is False:',
        '                    raise ValueError("Order rejected by RiskManager")',
        '                    ',
        '            if hasattr(self.risk_manager, "check_daily_loss_limit"):',
        '                if not self.risk_manager.check_daily_loss_limit():',
        '                    raise ValueError("Daily loss limit exceeded")',
        '                    ',
        '        if stop_loss is not None and p > 0:',
        '            sl = float(stop_loss)',
        '            if side_str == "BUY" and sl >= p:',
        '                raise ValueError("Stop loss for BUY must be lower than price")',
        '            if side_str == "SELL" and sl <= p:',
        '                raise ValueError("Stop loss for SELL must be higher than price")',
    ]
    
    new_lines = lines[:start_idx] + new_method + lines[end_idx:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print("✅ SUCCESS: _validate_order dynamically adapted to RiskManager signature!")
else:
    print("❌ ERROR: _validate_order method not found!")
