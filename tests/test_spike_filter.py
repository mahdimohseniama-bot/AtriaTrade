import pytest
from src.core.spike_filter import SpikeFilter


def test_spike_filter_normal_flow():
    sf = SpikeFilter(window_size=5, max_deviation_pct=0.05)
    
    # 1. تیک اول
    r1 = sf.process_tick(100.0)
    assert r1["is_valid"] is True
    assert r1["sanitized_price"] == 100.0

    # 2. نوسان عادی (102.0 -> 2% انحراف)
    r2 = sf.process_tick(102.0)
    assert r2["is_valid"] is True
    assert r2["sanitized_price"] == 102.0


def test_spike_filter_rejects_flash_spike():
    sf = SpikeFilter(window_size=5, max_deviation_pct=0.05, confirmation_count=2)
    for p in [100.0, 100.5, 99.5, 100.2, 100.0]:
        sf.process_tick(p)

    # اسپایک کاذب ناگهانی به 130.0 (30% انحراف)
    r_spike = sf.process_tick(130.0)
    assert r_spike["is_valid"] is False
    assert r_spike["sanitized_price"] == 100.0
    assert "SPIKE_REJECTED" in r_spike["reason"]

    # بازگشت بلافاصله به قیمت عادی 100.1
    r_back = sf.process_tick(100.1)
    assert r_back["is_valid"] is True
    assert r_back["sanitized_price"] == 100.1


def test_spike_filter_confirms_real_breakout():
    sf = SpikeFilter(window_size=5, max_deviation_pct=0.05, confirmation_count=2)
    for p in [100.0, 100.0, 100.0]:
        sf.process_tick(p)

    # پرش اول به 110.0 (۱۰٪ انحراف -> رد به عنوان اسپایک در اولین تیک)
    r1 = sf.process_tick(110.0)
    assert r1["is_valid"] is False

    # تیک دوم در 110.5 (تأیید شکست و تغییر جهت واقعی بازار)
    r2 = sf.process_tick(110.5)
    assert r2["is_valid"] is True
    assert r2["sanitized_price"] == 110.5
    assert r2["reason"] == "CONFIRMED_BREAKOUT"
