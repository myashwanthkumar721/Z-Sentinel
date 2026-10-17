from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:
    return max(low, min(high, float(value)))


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)

        if result != result:
            return default

        return result

    except (TypeError, ValueError):
        return default