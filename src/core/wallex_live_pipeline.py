import logging
from typing import Any, Dict

logger = logging.getLogger("AtriaTrade.WallexLivePipeline")

class WallexLivePipeline:
    def __init__(self, executor: Any, syncer: Any):
        self.executor = executor
        self.syncer = syncer

    def execute_order_with_balance_check(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Syncs balance, validates sufficiency, and executes order if safe.
        """
        # 1. Sync Balances
        balances = self.syncer.fetch_balances()
        
        # 2. Basic Validation (Assume base currency vs quote currency logic)
        # Simplified: Check if we have enough quote currency for Buy order (symbol: BASE/QUOTE)
        base, quote = symbol.split('/')
        cost = amount * price
        
        if side.upper() == 'BUY':
            if not self.syncer.has_sufficient_balance(quote, cost):
                logger.error(f"Insufficient {quote} balance for BUY order")
                return {"success": False, "error": "Insufficient funds"}
        elif side.upper() == 'SELL':
            if not self.syncer.has_sufficient_balance(base, amount):
                logger.error(f"Insufficient {base} balance for SELL order")
                return {"success": False, "error": "Insufficient funds"}

        # 3. Execute
        return self.executor.place_order(symbol=symbol, side=side, amount=amount, price=price)
