import sys
from src.core.ote_engine import OTEEngine, TradeDirection, MarketZone
from src.core.fvg_detector import FVGDetector, FVGType, Candle

def test_ote():
    print("[-] Testing OTE Engine...")
    engine = OTEEngine()
    
    # تست با TradeDirection.LONG
    profile_long = engine.calculate_ote(swing_low=60000.0, swing_high=70000.0, direction=TradeDirection.LONG)
    assert profile_long.direction == TradeDirection.LONG, "Direction mismatch in LONG"
    assert profile_long.equilibrium == 65000.0, f"Equilibrium expected 65000, got {profile_long.equilibrium}"
    assert profile_long.ote_618 == 63820.0, f"OTE 0.618 expected 63820, got {profile_long.ote_618}"
    
    # تست با TradeDirection.SHORT
    profile_short = engine.calculate_ote(swing_low=60000.0, swing_high=70000.0, direction=TradeDirection.SHORT)
    assert profile_short.direction == TradeDirection.SHORT, "Direction mismatch in SHORT"
    
    # بررسی زون مارکت (Discount vs Premium)
    zone_discount = engine.get_market_zone(price=62000.0, swing_low=60000.0, swing_high=70000.0)
    assert zone_discount == MarketZone.DISCOUNT, f"Expected DISCOUNT, got {zone_discount}"
    
    zone_premium = engine.get_market_zone(price=68000.0, swing_low=60000.0, swing_high=70000.0)
    assert zone_premium == MarketZone.PREMIUM, f"Expected PREMIUM, got {zone_premium}"
    
    print(" [✓] OTE Engine passed successfully!")

def test_fvg():
    print("[-] Testing FVG Detector...")
    detector = FVGDetector(min_gap_percent=0.0)
    
    # الگوی ۳ کندلی صعودی که بین کندل ۱ و ۳ گپ ایجاد می‌شود:
    # Candle 1 High = 105, Candle 3 Low = 110 -> گپ صعودی بین 105 تا 110
    candles = [
        Candle(open=100.0, high=105.0, low=99.0, close=104.0),
        Candle(open=104.0, high=115.0, low=103.0, close=114.0),
        Candle(open=114.0, high=120.0, low=110.0, close=118.0)
    ]
    
    fvgs = detector.detect_fvgs(candles)
    assert len(fvgs) == 1, f"Expected 1 FVG, found {len(fvgs)}"
    fvg = fvgs[0]
    assert fvg.gap_type == FVGType.BULLISH, f"Expected BULLISH, got {fvg.gap_type}"
    assert fvg.bottom_price == 105.0, f"Expected bottom 105.0, got {fvg.bottom_price}"
    assert fvg.top_price == 110.0, f"Expected top 110.0, got {fvg.top_price}"
    
    # تست میتیگیشن (آیا قیمت گپ را پر کرده است؟)
    mitigating_candle = [Candle(open=118.0, high=119.0, low=104.0, close=106.0)]
    is_mitigated = detector.check_mitigation(fvg, mitigating_candle)
    assert is_mitigated is True, "FVG should be mitigated"
    
    print(" [✓] FVG Detector passed successfully!")

if __name__ == "__main__":
    try:
        test_ote()
        test_fvg()
        print("\n==========================================")
        print("  STAGE 6 (SMC CORE) VERIFIED SUCCESSFULLY!")
        print("==========================================")
    except Exception as e:
        print(f"\n[X] Test Failed with error: {e}")
        sys.exit(1)
