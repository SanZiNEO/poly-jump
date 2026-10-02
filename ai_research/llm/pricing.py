"""DeepSeek 价格与计费（人民币，元）。

价格来源：https://api-docs.deepseek.com/quick_start/pricing
空闲时段价格为高峰时段的一半。北京时间周一至周五（不含中国法定节假日）
9:00-12:00、14:00-18:00 为高峰时段；其余时段为空闲时段。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

# 每 1M token 价格（元）：(空闲时段, 高峰时段)
PRICES: dict[str, dict[str, tuple[float, float]]] = {
    "deepseek-flash": {
        "cache_hit": (0.02, 0.04),
        "cache_miss": (1.0, 2.0),
        "output": (4.0, 8.0),
    },
    "deepseek-v4-pro": {
        "cache_hit": (0.15, 0.30),
        "cache_miss": (4.5, 9.0),
        "output": (13.5, 27.0),
    },
}

# 高峰时段（北京时间，分钟）
PEAK_WINDOWS = ((9 * 60, 12 * 60), (14 * 60, 18 * 60))


def is_peak(when: datetime | None = None) -> bool:
    """判断是否处于高峰时段（周一至周五 9-12 / 14-18，北京时间）。"""
    now = when.astimezone(CST) if when else datetime.now(CST)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return any(start <= minutes < end for start, end in PEAK_WINDOWS)


def compute_cost(
    model: str,
    *,
    cache_hit: int = 0,
    cache_miss: int = 0,
    output: int = 0,
    when: datetime | None = None,
) -> float:
    """按 token 数计算本次调用费用（元）。"""
    table = PRICES.get(model)
    if table is None:
        raise KeyError(f"未知模型价格: {model}，可选: {list(PRICES)}")
    idx = 1 if is_peak(when) else 0
    return (
        cache_hit / 1e6 * table["cache_hit"][idx]
        + cache_miss / 1e6 * table["cache_miss"][idx]
        + output / 1e6 * table["output"][idx]
    )
