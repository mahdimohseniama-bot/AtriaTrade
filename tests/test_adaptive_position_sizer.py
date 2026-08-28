import pytest
from src.core.adaptive_position_sizer import AdaptivePositionSizer


def test_sizer_invalid_inputs():
    sizer = AdaptivePositionSizer()
    res = sizer.calculate_size(capital=0, entry_price=100, stop_loss_price=95)
    assert res["valid"] is False
    assert res["reason"] == "INVALID_PRICE_OR_CAPITAL"


def test_sizer_basic_calculation():
    sizer = AdaptivePositionSizer(default_risk_per_trade_pct=1.0)
    # سرمایه ۱۰۰۰۰ دلار، ۱٪ ریسک = ۱۰۰ دلار. فاصله ورود ۱۰۰ تا استاپ ۹۸ = ۲ دلار به ازای هر واحد -> حجم ۵۰
    res = sizer.calculate_size(capital=10000.0, entry_price=100.0, stop_loss_price=98.0)
    assert res["valid"] is True
    assert res["size"] == pytest.approx(50.0)
    assert res["risk_amount"] == pytest.approx(100.0)


def test_sizer_high_volatility_dampening():
    sizer = AdaptivePositionSizer(default_risk_per_trade_pct=1.0)
    # ATR بالا (۴ دلار روی قیمت ۱۰۰ = ۴٪ نوسان) -> ضریب ۰.۷۵ ریسک
    res = sizer.calculate_size(capital=10000.0, entry_price=100.0, stop_loss_price=98.0, atr_value=4.0)
    assert res["valid"] is True
    assert res["effective_risk_pct"] == pytest.approx(0.75)
    assert res["size"] == pytest.approx(37.5)


def test_sizer_max_position_cap():
    sizer = AdaptivePositionSizer(default_risk_per_trade_pct=2.0, max_position_size_pct=10.0)
    # فاصله استاپ بسیار کوچک (۰.۱ دلار)، بدون سقف حجم بسیار بزرگی می‌شد اما سقف ۱۰٪ سرمایه (۱۰۰۰ دلار) مهارش می‌کند
    res = sizer.calculate_size(capital=10000.0, entry_price=100.0, stop_loss_price=99.9)
    assert res["valid"] is True
    assert res["position_value"] == pytest.approx(1000.0)
    assert res["size"] == pytest.approx(10.0)
