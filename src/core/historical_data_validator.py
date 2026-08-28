from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

@dataclass
class ValidationIssue:
    code: str
    message: str
    index: Optional[int] = None
    field: Optional[str] = None
    raw_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "index": self.index,
            "field": self.field,
            "raw_value": self.raw_value,
        }

@dataclass
class ValidationReport:
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }

class HistoricalDataValidator:
    REQUIRED_FIELDS = ["timestamp", "open", "high", "low", "close", "volume"]

    def __init__(self, timeframe_minutes: Optional[int] = None):
        self.timeframe_minutes = timeframe_minutes

    def _parse_timestamp(self, ts_raw: Any) -> Optional[datetime]:
        if isinstance(ts_raw, (int, float)):
            try:
                # Milliseconds check
                if ts_raw > 1e11:
                    return datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
                return datetime.fromtimestamp(ts_raw, tz=timezone.utc)
            except Exception:
                return None
        if isinstance(ts_raw, str):
            try:
                # Handle ISO 8601 strings
                s = ts_raw.replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None
        if isinstance(ts_raw, datetime):
            if ts_raw.tzinfo is None:
                return ts_raw.replace(tzinfo=timezone.utc)
            return ts_raw
        return None

    def validate(self, candles: List[Dict[str, Any]]) -> ValidationReport:
        issues: List[ValidationIssue] = []

        if not candles or not isinstance(candles, list) or len(candles) == 0:
            issues.append(ValidationIssue(code="EMPTY_DATASET", message="Candle dataset is empty or invalid"))
            return ValidationReport(is_valid=False, issues=issues)

        parsed_datetimes = []
        seen_timestamps = set()

        for idx, candle in enumerate(candles):
            if not isinstance(candle, dict):
                issues.append(ValidationIssue(code="INVALID_CANDLE_FORMAT", message="Candle must be a dictionary", index=idx))
                continue

            # 1. Missing fields check
            for field_name in self.REQUIRED_FIELDS:
                if field_name not in candle or candle[field_name] is None:
                    if field_name == "volume" and candle.get(field_name) is None and "volume" in candle:
                        issues.append(ValidationIssue(code="INVALID_VOLUME_TYPE", message="Volume is None", index=idx, field="volume", raw_value=None))
                    else:
                        issues.append(ValidationIssue(code="MISSING_FIELD", message=f"Missing field: {field_name}", index=idx, field=field_name))

            # 2. Field types and values validation
            prices = {}
            for p_field in ["open", "high", "low", "close"]:
                if p_field in candle and candle[p_field] is not None:
                    val = candle[p_field]
                    if not isinstance(val, (int, float)) or isinstance(val, bool):
                        issues.append(ValidationIssue(code="INVALID_PRICE_TYPE", message=f"Field {p_field} is not a numeric value", index=idx, field=p_field, raw_value=val))
                    else:
                        if val <= 0:
                            issues.append(ValidationIssue(code="INVALID_PRICE", message=f"Price {p_field} must be positive (> 0)", index=idx, field=p_field, raw_value=val))
                        else:
                            prices[p_field] = float(val)

            if "volume" in candle and candle["volume"] is not None:
                vol = candle["volume"]
                if not isinstance(vol, (int, float)) or isinstance(vol, bool):
                    issues.append(ValidationIssue(code="INVALID_VOLUME_TYPE", message="Volume must be numeric", index=idx, field="volume", raw_value=vol))
                else:
                    if vol < 0:
                        issues.append(ValidationIssue(code="INVALID_VOLUME", message="Volume cannot be negative", index=idx, field="volume", raw_value=vol))

            # 3. High/Low relationships check
            if len(prices) == 4:
                o, h, l, c = prices["open"], prices["high"], prices["low"], prices["close"]
                if h < o or h < c:
                    issues.append(ValidationIssue(code="HIGH_LESS_THAN_OPEN_OR_CLOSE", message=f"High ({h}) is less than Open ({o}) or Close ({c})", index=idx))
                if l > o or l > c:
                    issues.append(ValidationIssue(code="LOW_GREATER_THAN_OPEN_OR_CLOSE", message=f"Low ({l}) is greater than Open ({o}) or Close ({c})", index=idx))
                if h < l:
                    issues.append(ValidationIssue(code="HIGH_LESS_THAN_LOW", message=f"High ({h}) is less than Low ({l})", index=idx))

            # 4. Timestamp check
            if "timestamp" in candle and candle["timestamp"] is not None:
                raw_ts = candle["timestamp"]
                dt = self._parse_timestamp(raw_ts)
                if dt is None:
                    issues.append(ValidationIssue(code="INVALID_TIMESTAMP_FORMAT", message="Invalid timestamp format", index=idx, field="timestamp", raw_value=raw_ts))
                    parsed_datetimes.append(None)
                else:
                    if dt in seen_timestamps:
                        issues.append(ValidationIssue(code="DUPLICATE_TIMESTAMP", message=f"Duplicate timestamp detected: {raw_ts}", index=idx, field="timestamp", raw_value=raw_ts))
                    else:
                        seen_timestamps.add(dt)
                    parsed_datetimes.append(dt)
            else:
                parsed_datetimes.append(None)

        # 5. Temporal sequence and Gap check
        valid_dts = [(i, dt) for i, dt in enumerate(parsed_datetimes) if dt is not None]
        for k in range(len(valid_dts) - 1):
            curr_idx, curr_dt = valid_dts[k]
            next_idx, next_dt = valid_dts[k + 1]

            if next_dt < curr_dt:
                issues.append(ValidationIssue(code="UNSORTED_TIMESTAMPS", message=f"Candle at index {next_idx} timestamp is earlier than index {curr_idx}", index=next_idx))

            if self.timeframe_minutes is not None and next_dt > curr_dt:
                expected_delta = timedelta(minutes=self.timeframe_minutes)
                actual_delta = next_dt - curr_dt
                if actual_delta > expected_delta:
                    issues.append(ValidationIssue(code="MISSING_CANDLE_GAP", message=f"Data gap detected between {curr_dt} and {next_dt}", index=next_idx))

        is_valid = len(issues) == 0
        return ValidationReport(is_valid=is_valid, issues=issues)
