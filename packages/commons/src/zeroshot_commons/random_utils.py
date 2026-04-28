from __future__ import annotations

import random

MAX_SAFE_INTEGER = 9_007_199_254_740_991


def random_int(min_value: int | None = None, max_value: int | None = None) -> int:
    lower = 0 if min_value is None else min_value
    upper = MAX_SAFE_INTEGER if max_value is None else max_value
    return random.randint(lower, upper)
