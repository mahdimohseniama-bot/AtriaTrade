import logging
from typing import Dict, Any, Optional
from src.core.wallex_resilient_pipeline import WallexResilientPipeline
from src.core.risk_manager import RiskManager

logger = logging.getLogger("LiveExecutionManager")

class LiveExecutionManager:
    def __init__(self, pipeline: WallexResilientPipeline, risk_manager: RiskManager):
        self.pipeline = pipeline
        self.risk_manager = risk_manager

    def execute_with_guard(
        self,
        client_order_id: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        exchange_order_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validates risk before allowing the pipeline to send the order.
        """
        # 1. Check Risk Constraints
        risk_status = self.risk_manager.validate_order(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity
        )

        if not risk_status["permitted"]:
            logger.error(f"Execution rejected by RiskManager: {risk_status['reason']}")
            return {
                "status": "REJECTED_BY_RISK",
                "client_order_id": client_order_id,
                "reason": risk_status["reason"]
            }

        # 2. Proceed to Resilient Pipeline
        logger.info(f"Risk check passed. Executing order {client_order_id}")
        return self.pipeline.submit_resilient_order(
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            exchange_order_func=exchange_order_func,
            *args,
            **kwargs
        )
