import pytest

from src.analysis.signal_generator import SignalGenerator


def make_candle(
    sma_5=100.0,
    sma_20=95.0,
    rsi=55.0,
    macd=2.0,
    macd_signal=1.0,
):
    return {
        "timestamp": 1700000000000,
        "open": 100.0,
        "high": 105.0,
        "low": 98.0,
        "close": 102.0,
        "volume": 10.0,
        "indicators": {
            "sma_5": sma_5,
            "sma_20": sma_20,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
        },
    }


def test_buy_signal_is_generated_for_bullish_conditions():
    generator = SignalGenerator()

    result = generator.generate(
        [make_candle(sma_5=105.0, sma_20=100.0, rsi=55.0, macd=2.0, macd_signal=1.0)],
        symbol="BTC/USDT",
    )

    assert result["signal"] == "BUY"
    assert result["confidence"] == 1.0
    assert result["symbol"] == "BTC/USDT"
    assert result["price"] == 102.0
    assert len(result["reasons"]) == 3


def test_sell_signal_is_generated_for_bearish_conditions():
    generator = SignalGenerator()

    result = generator.generate(
        [make_candle(sma_5=90.0, sma_20=100.0, rsi=75.0, macd=-2.0, macd_signal=-1.0)]
    )

    assert result["signal"] == "SELL"
    assert result["confidence"] == 1.0
    assert len(result["reasons"]) == 3


def test_hold_signal_is_generated_for_mixed_conditions():
    generator = SignalGenerator()

    result = generator.generate(
        [make_candle(sma_5=105.0, sma_20=100.0, rsi=75.0, macd=-2.0, macd_signal=-1.0)]
    )

    assert result["signal"] == "HOLD"
    assert result["confidence"] == pytest.approx(2 / 3)
    assert "mixed" in result["reasons"][0].lower()


def test_hold_signal_is_generated_when_indicator_data_is_incomplete():
    generator = SignalGenerator()
    candle = make_candle()
    candle["indicators"]["macd"] = None

    result = generator.generate([candle])

    assert result["signal"] == "HOLD"
    assert result["confidence"] == 0.0
    assert "insufficient" in result["reasons"][0].lower()


def test_generate_uses_only_the_latest_analyzed_candle():
    generator = SignalGenerator()

    older_bullish_candle = make_candle(
        sma_5=105.0,
        sma_20=100.0,
        rsi=55.0,
        macd=2.0,
        macd_signal=1.0,
    )
    latest_bearish_candle = make_candle(
        sma_5=90.0,
        sma_20=100.0,
        rsi=75.0,
        macd=-2.0,
        macd_signal=-1.0,
    )

    result = generator.generate([older_bullish_candle, latest_bearish_candle])

    assert result["signal"] == "SELL"


def test_empty_candle_list_is_rejected():
    generator = SignalGenerator()

    with pytest.raises(ValueError, match="must not be empty"):
        generator.generate([])


def test_non_list_candles_input_is_rejected():
    generator = SignalGenerator()

    with pytest.raises(TypeError, match="must be a list"):
        generator.generate({"indicators": {}})


def test_missing_indicators_dictionary_is_rejected():
    generator = SignalGenerator()

    with pytest.raises(ValueError, match="indicators dictionary"):
        generator.generate([{"close": 100.0}])


def test_invalid_rsi_configuration_is_rejected():
    with pytest.raises(ValueError, match="rsi_oversold must be lower"):
        SignalGenerator(
            {
                "rsi_oversold": 80.0,
                "rsi_overbought": 70.0,
            }
        )


def test_invalid_minimum_confidence_is_rejected():
    with pytest.raises(ValueError, match="minimum_confidence must be between"):
        SignalGenerator({"minimum_confidence": 1.1})


def test_custom_confidence_threshold_is_applied():
    generator = SignalGenerator({"minimum_confidence": 1.0})

    result = generator.generate(
        [make_candle(sma_5=105.0, sma_20=100.0, rsi=55.0, macd=2.0, macd_signal=1.0)]
    )

    assert result["signal"] == "BUY"
    assert result["confidence"] == 1.0
