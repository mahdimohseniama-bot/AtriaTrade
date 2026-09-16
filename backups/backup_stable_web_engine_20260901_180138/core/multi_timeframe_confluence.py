"""
Multi-Timeframe Trend & Momentum Confluence Engine for AtriaTrade.
Calculates alignment and weighted confluence scores across multiple timeframes.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TimeframeSignal:
    timeframe: str          # e.g., '1h', '15m', '5m'
    trend_direction: int    # 1 for Bullish, -1 for Bearish, 0 for Neutral
    momentum_score: float   # -1.0 to +1.0 (e.g. from RSI / MACD / Stoch)
    weight: float = 1.0     # Importance weight of this timeframe


@dataclass(frozen=True)
class ConfluenceEvaluation:
    overall_direction: int      # 1 (Strong Buy), -1 (Strong Sell), 0 (No Trade / Conflict)
    confluence_score: float     # -1.0 to +1.0
    is_trend_aligned: bool      # True if HTF (Higher Timeframe) supports Trigger TF
    agreement_ratio: float      # Percentage of agreement across timeframes (0.0 to 1.0)
    rejection_reason: Optional[str] = None


class MultiTimeframeConfluenceEngine:
    """
    Evaluates multi-timeframe alignment to filter out counter-trend trades
    and false breakouts.
    """

    def __init__(self, min_confluence_threshold: float = 0.50, min_agreement_ratio: float = 0.60):
        if not (0.0 < min_confluence_threshold <= 1.0):
            raise ValueError("min_confluence_threshold باید بین 0.0 و 1.0 باشد")
        if not (0.0 < min_agreement_ratio <= 1.0):
            raise ValueError("min_agreement_ratio باید بین 0.0 و 1.0 باشد")

        self.min_confluence_threshold = min_confluence_threshold
        self.min_agreement_ratio = min_agreement_ratio

    def evaluate_confluence(self, signals: Dict[str, TimeframeSignal], trigger_tf: str = "5m") -> ConfluenceEvaluation:
        if not signals:
            raise ValueError("لیست سیگنال‌های تایم‌فریم نمی‌تواند خالی باشد")

        if trigger_tf not in signals:
            raise ValueError(f"سیگنال تایم‌فریم تریگر '{trigger_tf}' یافت نشد")

        total_weight = 0.0
        weighted_score = 0.0
        agree_count = 0
        trigger_signal = signals[trigger_tf]

        for tf, sig in signals.items():
            if sig.trend_direction not in (-1, 0, 1):
                raise ValueError(f"trend_direction نامعتبر برای {tf}: {sig.trend_direction}")
            if not (-1.0 <= sig.momentum_score <= 1.0):
                raise ValueError(f"momentum_score باید بین -1.0 و +1.0 باشد برای {tf}")
            if sig.weight <= 0:
                raise ValueError(f"وزن تایم‌فریم {tf} باید بزرگتر از صفر باشد")

            # ترکیب ترند و مومنتوم هر تایم فریم
            tf_composite = (sig.trend_direction * 0.6) + (sig.momentum_score * 0.4)
            weighted_score += tf_composite * sig.weight
            total_weight += sig.weight

            # بررسی همسویی با جهت تریگر
            if trigger_signal.trend_direction != 0 and sig.trend_direction == trigger_signal.trend_direction:
                agree_count += 1

        confluence_score = round(weighted_score / total_weight, 4)
        agreement_ratio = round(agree_count / len(signals), 4)

        # ارزیابی نهایی
        rejection_reasons = []
        is_aligned = True

        if abs(confluence_score) < self.min_confluence_threshold:
            is_aligned = False
            rejection_reasons.append(f"امتیاز همگرایی ({confluence_score}) کمتر از حد آستانه ({self.min_confluence_threshold}) است")

        if agreement_ratio < self.min_agreement_ratio:
            is_aligned = False
            rejection_reasons.append(f"نسبت توافق تایم‌فریم‌ها ({agreement_ratio:.2f}) کمتر از حد مجاز ({self.min_agreement_ratio}) است")

        overall_dir = 0
        if is_aligned:
            overall_dir = 1 if confluence_score > 0 else -1

        reason_str = " | ".join(rejection_reasons) if rejection_reasons else None

        return ConfluenceEvaluation(
            overall_direction=overall_dir,
            confluence_score=confluence_score,
            is_trend_aligned=is_aligned,
            agreement_ratio=agreement_ratio,
            rejection_reason=reason_str
        )
