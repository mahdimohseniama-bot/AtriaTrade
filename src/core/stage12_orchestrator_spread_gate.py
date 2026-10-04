import logging
from src.core.spread_fee_filter import SpreadFeeFilter

class Stage12OrchestratorSpreadGate:
    """
    Minimal orchestrator gate for Stage 12:
    blocks opening a position when spread/roundtrip cost is unfavorable.
    """
    def __init__(self, spread_filter: SpreadFeeFilter | None = None):
        self.logger = logging.getLogger("Stage12OrchestratorSpreadGate")
        self.spread_filter = spread_filter or SpreadFeeFilter(max_spread_pct=0.30, taker_fee_pct=0.2)

    def should_open_position(self, best_bid: float, best_ask: float) -> dict:
        decision = self.spread_filter.evaluate_spread(best_bid=best_bid, best_ask=best_ask)
        if not decision["allowed"]:
            return {
                "allowed": False,
                "reason": decision["reason"],
                "spread_pct": decision["spread_pct"],
                "est_roundtrip_cost_pct": decision.get("est_roundtrip_cost_pct", 0.0),
            }

        return {
            "allowed": True,
            "reason": "OK",
            "spread_pct": decision["spread_pct"],
            "est_roundtrip_cost_pct": decision["est_roundtrip_cost_pct"],
        }
