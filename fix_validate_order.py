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
        '    def _validate_order(self, order: Any) -> None:',
        '        # 1. اعتبارسنجی از طریق ماژول RiskManager',
        '        if hasattr(self, "risk_manager") and self.risk_manager is not None:',
        '            if hasattr(self.risk_manager, "validate_order"):',
        '                res = self.risk_manager.validate_order(order)',
        '                if isinstance(res, dict):',
        '                    if not res.get("is_valid", True):',
        '                        raise ValueError(res.get("reason", "Order rejected by RiskManager"))',
        '                elif res is False:',
        '                    raise ValueError("Order rejected by RiskManager")',
        '            ',
        '            if hasattr(self.risk_manager, "check_daily_loss_limit"):',
        '                if not self.risk_manager.check_daily_loss_limit():',
        '                    raise ValueError("Daily loss limit exceeded")',
        '            ',
        '        # 2. اعتبارسنجی منطقی حد ضرر (Stop Loss) بر اساس نوع سفارش',
        '        side_attr = getattr(order, "side", None)',
        '        side = str(getattr(side_attr, "value", side_attr)).upper() if side_attr else "BUY"',
        '        price = float(getattr(order, "price", 0.0))',
        '        ',
        '        if price == 0.0 and hasattr(order, "current_price") and getattr(order, "current_price") is not None:',
        '            price = float(getattr(order, "current_price"))',
        '            ',
        '        stop_loss = getattr(order, "stop_loss", None)',
        '        if stop_loss is not None and price > 0:',
        '            stop_loss = float(stop_loss)',
        '            if side == "BUY" and stop_loss >= price:',
        '                raise ValueError("Stop loss for BUY must be lower than price")',
        '            if side == "SELL" and stop_loss <= price:',
        '                raise ValueError("Stop loss for SELL must be higher than price")',
    ]
    
    new_lines = lines[:start_idx] + new_method + lines[end_idx:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print("✅ SUCCESS: _validate_order successfully updated with risk validations!")
else:
    print("❌ ERROR: _validate_order method not found!")
