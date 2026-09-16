import sys
from pathlib import Path

path = Path("src/core/order_executor.py")
text = path.read_text(encoding="utf-8")
lines = text.split("\n")

start_idx = -1
end_idx = -1

# پیدا کردن لاین شروع متد process_limit_order
for i, line in enumerate(lines):
    if line.startswith("    def process_limit_order("):
        start_idx = i
        break

# پیدا کردن لاین پایان متد (شروع متد بعدی)
if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("    def "):
            end_idx = i
            break

# جایگزینی متد با منطق صحیح شرط قیمت
if start_idx != -1 and end_idx != -1:
    new_method = [
        '    def process_limit_order(',
        '        self,',
        '        order_id: Any,',
        '        current_price: Optional[float] = None,',
        '    ) -> Any:',
        '        order = self._find_order(order_id)',
        '        if current_price is None:',
        '            return order',
        '            ',
        '        current_price = float(current_price)',
        '        order_price = float(getattr(order, "price", 0.0))',
        '        ',
        '        side_attr = getattr(order, "side", None)',
        '        side = str(getattr(side_attr, "value", side_attr)).upper() if side_attr else "BUY"',
        '        ',
        '        should_fill = False',
        '        if side == "BUY":',
        '            should_fill = current_price <= order_price',
        '        elif side == "SELL":',
        '            should_fill = current_price >= order_price',
        '        ',
        '        if not should_fill:',
        '            from src.core.order_manager import OrderStatus',
        '            setattr(order, "status", OrderStatus.PENDING)',
        '            self._set_order_fields(order, filled_price=None, filled_quantity=None)',
        '            return order',
        '            ',
        '        return self.execute_limit_order(',
        '            order_id=order_id,',
        '            execution_price=order_price,',
        '            current_price=current_price,',
        '        )'
    ]
    
    new_lines = lines[:start_idx] + new_method + lines[end_idx:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print("✅ SUCCESS: process_limit_order method successfully replaced!")
else:
    print(f"❌ ERROR: method markers not found! start={start_idx}, end={end_idx}")
