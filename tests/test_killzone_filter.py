from datetime import datetime, timezone
import pytest
from src.core.killzone_filter import (
    KillzoneFilter,
    SessionType
)


def test_london_open_killzone():
    filter_engine = KillzoneFilter()
    # 08:30 UTC -> London Killzone
    dt = datetime(2026, 8, 29, 8, 30, 0, tzinfo=timezone.utc)
    session, is_kz = filter_engine.get_current_session(dt)

    assert session == SessionType.LONDON_OPEN
    assert is_kz is True
    assert filter_engine.is_valid_killzone_entry(dt) is True


def test_new_york_am_killzone():
    filter_engine = KillzoneFilter()
    # 13:15 UTC -> NY Open Killzone
    dt = datetime(2026, 8, 29, 13, 15, 0, tzinfo=timezone.utc)
    session, is_kz = filter_engine.get_current_session(dt)

    assert session == SessionType.NY_OPEN_AM
    assert is_kz is True
    assert filter_engine.is_valid_killzone_entry(dt) is True


def test_asia_session_and_filter():
    filter_engine = KillzoneFilter()
    # 02:00 UTC -> Asia Accumulation
    dt = datetime(2026, 8, 29, 2, 0, 0, tzinfo=timezone.utc)
    session, is_kz = filter_engine.get_current_session(dt)

    assert session == SessionType.ASIA_ACCUMULATION
    assert is_kz is False
    # By default, Asia is not allowed for high-volatility breakout setups
    assert filter_engine.is_valid_killzone_entry(dt, allow_asia=False) is False
    assert filter_engine.is_valid_killzone_entry(dt, allow_asia=True) is True


def test_out_of_session():
    filter_engine = KillzoneFilter()
    # 22:00 UTC -> Out of Session (Dead zone)
    dt = datetime(2026, 8, 29, 22, 0, 0, tzinfo=timezone.utc)
    session, is_kz = filter_engine.get_current_session(dt)

    assert session == SessionType.OUT_OF_SESSION
    assert is_kz is False
    assert filter_engine.is_valid_killzone_entry(dt) is False
