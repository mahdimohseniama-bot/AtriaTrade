import asyncio
from src.core.event_pipeline import EventPipeline


def test_direct_sync_and_async_handlers():
    async def _test():
        pipeline = EventPipeline()
        sync_called = []
        async_called = []

        def sync_handler(payload):
            sync_called.append(payload["data"])

        async def async_handler(payload):
            await asyncio.sleep(0.001)
            async_called.append(payload["data"])

        pipeline.subscribe("MARKET_TICK", sync_handler)
        pipeline.subscribe("MARKET_TICK", async_handler)

        await pipeline.emit("MARKET_TICK", {"data": "tick_100"})

        assert sync_called == ["tick_100"]
        assert async_called == ["tick_100"]

    asyncio.run(_test())


def test_wildcard_subscription():
    async def _test():
        pipeline = EventPipeline()
        all_events = []

        def global_handler(payload):
            all_events.append(payload["name"])

        pipeline.subscribe("*", global_handler)
        await pipeline.emit("ORDER_SUBMITTED", {"name": "order_1"})
        await pipeline.emit("POSITION_CLOSED", {"name": "pos_1"})

        assert all_events == ["order_1", "pos_1"]

    asyncio.run(_test())


def test_unsubscribe_handler():
    async def _test():
        pipeline = EventPipeline()
        counter = []

        def handler(payload):
            counter.append(1)

        pipeline.subscribe("ALERT", handler)
        await pipeline.emit("ALERT", {})
        assert len(counter) == 1

        unsub_status = pipeline.unsubscribe("ALERT", handler)
        assert unsub_status is True

        await pipeline.emit("ALERT", {})
        assert len(counter) == 1

    asyncio.run(_test())


def test_queued_background_processing():
    async def _test():
        pipeline = EventPipeline()
        received = []

        async def handler(payload):
            received.append(payload["id"])

        pipeline.subscribe("SIGNAL_NEW", handler)
        pipeline.start()

        await pipeline.enqueue("SIGNAL_NEW", {"id": 1})
        await pipeline.enqueue("SIGNAL_NEW", {"id": 2})

        # فرصت برای پردازش تسک پس‌زمینه
        await asyncio.sleep(0.05)
        await pipeline.stop()

        assert received == [1, 2]

    asyncio.run(_test())
