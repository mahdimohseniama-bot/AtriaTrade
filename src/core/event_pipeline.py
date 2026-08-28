import asyncio
import logging
from typing import Callable, Dict, List, Any, Awaitable, Union

logger = logging.getLogger(__name__)

HandlerType = Callable[[Dict[str, Any]], Union[None, Awaitable[None]]]


class EventPipeline:
    """
    Asynchronous event bus and dispatcher for AtriaTrade.
    Enables decoupled publish-subscribe messaging between core components.
    """
    def __init__(self):
        self._handlers: Dict[str, List[HandlerType]] = {}
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Union[asyncio.Task, None] = None

    def subscribe(self, event_type: str, handler: HandlerType) -> None:
        """Registers a callback handler for a specific event type."""
        key = event_type.upper()
        if key not in self._handlers:
            self._handlers[key] = []
        if handler not in self._handlers[key]:
            self._handlers[key].append(handler)

    def unsubscribe(self, event_type: str, handler: HandlerType) -> bool:
        """Unregisters an event handler."""
        key = event_type.upper()
        if key in self._handlers and handler in self._handlers[key]:
            self._handlers[key].remove(handler)
            return True
        return False

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Dispatches an event directly and awaits all registered handlers concurrently."""
        key = event_type.upper()
        handlers = self._handlers.get(key, []) + self._handlers.get("*", [])
        if not handlers:
            return

        tasks = []
        for handler in handlers:
            try:
                res = handler(payload)
                if asyncio.iscoroutine(res):
                    tasks.append(res)
            except Exception as exc:
                logger.error(f"Sync handler error on event '{key}': {exc}")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Async handler error on event '{key}': {res}")

    async def enqueue(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Pushes an event into the asynchronous queue for background processing."""
        await self._queue.put((event_type.upper(), payload))

    async def _process_queue(self) -> None:
        """Background worker loop reading and dispatching events from queue."""
        while self._running:
            try:
                event_type, payload = await self._queue.get()
                await self.emit(event_type, payload)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Queue processing error: {exc}")

    def start(self) -> None:
        """Starts the background event processor."""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        """Gracefully stops the event pipeline and drains pending items."""
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
                self._worker_task = None
