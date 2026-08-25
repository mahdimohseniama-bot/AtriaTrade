from src.exchange.health import ExchangeHealthMonitor


class HealthyAdapter:
    def test_connection(self):
        return True


class UnhealthyAdapter:
    def test_connection(self):
        return False


class BrokenAdapter:
    def test_connection(self):
        raise ConnectionError("Temporary network failure")


class FakeExchangeFactory:
    adapters = {
        "HEALTHY": HealthyAdapter(),
        "UNHEALTHY": UnhealthyAdapter(),
        "BROKEN": BrokenAdapter(),
    }

    @classmethod
    def create(cls, exchange_name):
        if exchange_name not in cls.adapters:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

        return cls.adapters[exchange_name]


def test_check_exchange_returns_healthy_status():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status = monitor.check_exchange("healthy")

    assert status.exchange_name == "HEALTHY"
    assert status.is_healthy is True
    assert status.error_type is None
    assert status.error_message is None
    assert status.response_time_ms >= 0
    assert "T" in status.checked_at


def test_check_exchange_returns_unhealthy_status_when_connection_is_false():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status = monitor.check_exchange("unhealthy")

    assert status.exchange_name == "UNHEALTHY"
    assert status.is_healthy is False
    assert status.error_type == "ConnectionCheckFailed"
    assert "returned False" in status.error_message
    assert status.response_time_ms >= 0


def test_check_exchange_captures_connection_exception():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status = monitor.check_exchange("broken")

    assert status.exchange_name == "BROKEN"
    assert status.is_healthy is False
    assert status.error_type == "ConnectionError"
    assert status.error_message == "Temporary network failure"
    assert status.response_time_ms >= 0


def test_check_exchange_captures_unknown_exchange_error():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status = monitor.check_exchange("unknown")

    assert status.exchange_name == "UNKNOWN"
    assert status.is_healthy is False
    assert status.error_type == "ValueError"
    assert "Unsupported exchange: UNKNOWN" in status.error_message


def test_check_exchanges_returns_independent_results():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    results = monitor.check_exchanges(
        ["healthy", "unhealthy", "broken"],
    )

    assert set(results.keys()) == {"HEALTHY", "UNHEALTHY", "BROKEN"}
    assert results["HEALTHY"].is_healthy is True
    assert results["UNHEALTHY"].is_healthy is False
    assert results["BROKEN"].is_healthy is False


def test_health_status_can_be_converted_to_dictionary():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status_data = monitor.check_exchange("healthy").to_dict()

    assert status_data["exchange_name"] == "HEALTHY"
    assert status_data["is_healthy"] is True
    assert status_data["error_type"] is None


def test_empty_exchange_name_is_reported_as_structured_error():
    monitor = ExchangeHealthMonitor(exchange_factory=FakeExchangeFactory)

    status = monitor.check_exchange("   ")

    assert status.exchange_name == "   "
    assert status.is_healthy is False
    assert status.error_type == "ValueError"
    assert status.error_message == "Exchange name cannot be empty."
