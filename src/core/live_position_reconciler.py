import logging
from typing import Dict, Any, List
from src.core.position_tracker import PositionTracker
from src.adapters.wallex_resilient_session import WallexResilientSession

logger = logging.getLogger("LivePositionReconciler")

class LivePositionReconciler:
    def __init__(self, session: WallexResilientSession, position_tracker: PositionTracker):
        self.session = session
        self.tracker = position_tracker

    def reconcile_live_positions(self, fetch_positions_func) -> Dict[str, Any]:
        """
        Fetches real positions from exchange and forces sync with local PositionTracker.
        """
        res = self.session.request_with_retry("get_positions", fetch_positions_func)
        
        if not res["success"]:
            logger.error("Failed to fetch live positions for reconciliation.")
            return {"synced": False, "error": res.get("error")}

        live_positions = res["data"] # Expected list of {symbol: str, amount: float}
        
        # Sync tracker with live data
        for pos in live_positions:
            self.tracker.update_position(
                symbol=pos["symbol"],
                amount=pos["amount"]
            )
            
        logger.info(f"Reconciled {len(live_positions)} positions with exchange.")
        return {"synced": True, "count": len(live_positions)}
