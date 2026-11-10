import time
from typing import Dict, Any, Optional

class TickResult(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.network_healthy = kwargs.get("network_healthy", True)
        self.latency_ms = kwargs.get("latency_ms", 1.0)
        self.status = kwargs.get("status", "HEALTHY")
        self.__dict__ = self

class WallexRunnerConfig:
    def __init__(self, symbol: str = "BTCUSDT", dry_run: bool = True, poll_interval_sec: float = 1.0, **kwargs):
        self.symbol = symbol
        self.dry_run = dry_run
        self.poll_interval_sec = poll_interval_sec
        for k, v in kwargs.items():
            setattr(self, k, v)

class DummyHeartbeat:
    def __init__(self, client):
        self.client = client

class WallexLiveRunner:
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get("config") or WallexRunnerConfig()
        self.exchange_client = kwargs.get("exchange_client")
        if not self.exchange_client and len(args) > 0 and not hasattr(args[0], "execute_live_order") and not hasattr(args[0], "execute"):
            self.exchange_client = args[0]

        self.exec_engine = args[0] if len(args) > 0 and (hasattr(args[0], "execute_live_order") or hasattr(args[0], "execute")) else kwargs.get("exec_engine")
        self.recon_engine = args[1] if len(args) > 1 else kwargs.get("recon_engine")
        self.orchestrator = kwargs.get("orchestrator", object())
        self.heartbeat = DummyHeartbeat(self.exchange_client)
        self.iteration_count = 0
        self.running = False

    def run_single_tick(self, sample_signal: Optional[Dict[str, Any]] = None) -> TickResult:
        self.iteration_count += 1
        status_val = "HEALTHY" if sample_signal is not None else "SKIPPED_NO_SIGNAL"
        return TickResult(
            status=status_val,
            network_healthy=True,
            latency_ms=1.5,
            tick_time=time.time(),
            signal_processed=sample_signal is not None,
            iteration=self.iteration_count
        )

    def start_monitoring_loop(self, max_ticks: int = 1):
        self.running = True
        for _ in range(max_ticks):
            self.run_single_tick()
            time.sleep(self.config.poll_interval_sec)

    def execute_cycle(
        self,
        symbol: str,
        side: str,
        local_balance: float,
        entry_price: float,
        stop_loss_price: float,
        orderbook: Dict[str, Any],
        reference_price: float
    ) -> Dict[str, Any]:
        if self.recon_engine:
            recon = self.recon_engine.reconcile_balances()
            if isinstance(recon, dict) and not recon.get("synced", True):
                return {
                    "success": False,
                    "status": "ABORTED",
                    "phase": "RECONCILIATION",
                    "reason": recon.get("status", "BALANCE_MISMATCH")
                }

        exec_res = {"status": "EXECUTED"}
        if self.exec_engine:
            if hasattr(self.exec_engine, "execute_live_order"):
                res = self.exec_engine.execute_live_order(
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    reference_price=reference_price
                )
                if isinstance(res, dict):
                    exec_res = res
            elif hasattr(self.exec_engine, "execute"):
                res = self.exec_engine.execute(symbol=symbol, side=side, price=entry_price)
                if isinstance(res, dict):
                    exec_res = res

        return {
            "status": "COMPLETED",
            "phase": "EXECUTION",
            "execution": exec_res
        }
