from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional

from src.exchange.factory import ExchangeFactory


@dataclass(frozen=True)
class ExchangeHealthStatus:
    """
    نتیجه بررسی سلامت یک صرافی.

    این ماژول فقط وضعیت اتصال را بررسی می‌کند و هیچ عملیات مالی،
    ثبت سفارش، واریز یا برداشت انجام نمی‌دهد.
    """

    exchange_name: str
    is_healthy: bool
    checked_at: str
    response_time_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """تبدیل وضعیت سلامت به دیکشنری مناسب API یا داشبورد."""
        return asdict(self)


class ExchangeHealthMonitor:
    """
    مانیتور سلامت اتصال Adapterهای صرافی.

    فقط متد test_connection را فراخوانی می‌کند.
    هیچ سفارش واقعی یا آزمایشی در این ماژول ثبت نمی‌شود.
    """

    def __init__(self, exchange_factory=ExchangeFactory):
        self.exchange_factory = exchange_factory

    @staticmethod
    def _utc_now_iso() -> str:
        """برگرداندن زمان فعلی UTC در قالب ISO 8601."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_exchange_name(exchange_name: str) -> str:
        """
        اعتبارسنجی و استانداردسازی نام صرافی.

        نمونه:
        ' nobitex ' -> 'NOBITEX'
        """
        if not isinstance(exchange_name, str):
            raise ValueError("Exchange name must be a string.")

        normalized_name = exchange_name.strip().upper()

        if not normalized_name:
            raise ValueError("Exchange name cannot be empty.")

        return normalized_name

    @staticmethod
    def _safe_exchange_name(exchange_name: object) -> str:
        """
        ساخت نام مناسب برای گزارش خطا.

        قواعد:
        - ورودی معتبر یا نام صرافی ناشناخته استاندارد می‌شود:
          'broken' -> 'BROKEN'
          ' unknown ' -> 'UNKNOWN'
        - ورودی فقط شامل فاصله، بدون تغییر نگه داشته می‌شود تا
          عین مقدار ورودی در خروجی خطای ساختاریافته ثبت شود.
        - ورودی غیررشته‌ای به رشته تبدیل می‌شود.
        """
        if not isinstance(exchange_name, str):
            return str(exchange_name)

        normalized_name = exchange_name.strip().upper()

        if not normalized_name:
            return exchange_name

        return normalized_name

    def check_exchange(self, exchange_name: str) -> ExchangeHealthStatus:
        """
        بررسی سلامت یک صرافی.

        همهٔ خطاها، از جمله ورودی خالی، صرافی ناشناخته و خطای اتصال،
        به خروجی ساختاریافته ExchangeHealthStatus تبدیل می‌شوند.
        """
        checked_at = self._utc_now_iso()
        started_at = time.perf_counter()
        reported_exchange_name = self._safe_exchange_name(exchange_name)

        try:
            normalized_name = self._normalize_exchange_name(exchange_name)
            adapter = self.exchange_factory.create(normalized_name)
            is_connected = bool(adapter.test_connection())

            response_time_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            if is_connected:
                return ExchangeHealthStatus(
                    exchange_name=normalized_name,
                    is_healthy=True,
                    checked_at=checked_at,
                    response_time_ms=response_time_ms,
                )

            return ExchangeHealthStatus(
                exchange_name=normalized_name,
                is_healthy=False,
                checked_at=checked_at,
                response_time_ms=response_time_ms,
                error_type="ConnectionCheckFailed",
                error_message=(
                    "The exchange adapter returned False from "
                    "test_connection()."
                ),
            )

        except Exception as exc:
            response_time_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            return ExchangeHealthStatus(
                exchange_name=reported_exchange_name,
                is_healthy=False,
                checked_at=checked_at,
                response_time_ms=response_time_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def check_exchanges(
        self,
        exchange_names: Iterable[str],
    ) -> Dict[str, ExchangeHealthStatus]:
        """
        بررسی مستقل چند صرافی.

        خطای هر صرافی باعث توقف بررسی صرافی‌های دیگر نمی‌شود.
        """
        results: Dict[str, ExchangeHealthStatus] = {}

        for exchange_name in exchange_names:
            status = self.check_exchange(exchange_name)
            results[status.exchange_name] = status

        return results
