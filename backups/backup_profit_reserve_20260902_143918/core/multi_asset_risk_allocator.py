from typing import Dict, List, Any


class MultiAssetRiskAllocator:
    """
    توزیع‌کننده هوشمند ریسک برای پورتفولیوهای چند دارایی (کریپتو، طلا، ارز).
    از اورلود شدن ریسک روی دارایی‌های با همبستگی بالا جلوگیری می‌کند.
    """
    def __init__(self, max_total_portfolio_risk_pct: float = 5.0, max_single_asset_risk_pct: float = 2.0):
        self.max_total_risk = max_total_portfolio_risk_pct
        self.max_single_risk = max_single_asset_risk_pct

    def evaluate_allocation(self, current_open_risks: Dict[str, float], proposed_asset: str, proposed_risk_pct: float, correlation_group: str = "CRYPTO") -> Dict[str, Any]:
        """
        بررسی امکان تخصیص ریسک به دارایی جدید بر اساس ریسک کل و سقف مجاز تک‌دارایی.
        """
        current_total_risk = sum(current_open_risks.values())
        asset_current_risk = current_open_risks.get(proposed_asset, 0.0)

        # بررسی سقف ریسک تک دارایی
        if asset_current_risk + proposed_risk_pct > self.max_single_risk:
            allowed_single_risk = max(0.0, self.max_single_risk - asset_current_risk)
            if allowed_single_risk <= 0.0:
                return {
                    "approved": False,
                    "allocated_risk_pct": 0.0,
                    "reason": f"Max single asset risk limit reached for {proposed_asset}."
                }
            proposed_risk_pct = allowed_single_risk

        # بررسی سقف ریسک کل سبد
        if current_total_risk + proposed_risk_pct > self.max_total_risk:
            allowed_total_risk = max(0.0, self.max_total_risk - current_total_risk)
            if allowed_total_risk <= 0.0:
                return {
                    "approved": False,
                    "allocated_risk_pct": 0.0,
                    "reason": "Max portfolio risk limit reached."
                }
            proposed_risk_pct = allowed_total_risk

        return {
            "approved": True,
            "allocated_risk_pct": round(proposed_risk_pct, 4),
            "new_total_risk_pct": round(current_total_risk + proposed_risk_pct, 4),
            "reason": "Allocation approved."
        }
