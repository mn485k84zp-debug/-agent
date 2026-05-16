from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from src.core.exceptions import TransientToolError

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    retries: int = 3,
    base_delay: float = 0.8,
    max_delay: float = 4.0,
) -> T:
    """对临时性错误执行有限次指数退避重试。

    这里只对明确标记为临时性的问题进行重试，避免把确定性错误无意义地重复执行。
    """

    attempt = 0
    while True:
        try:
            return func()
        except TransientToolError:
            attempt += 1
            if attempt > retries:
                raise

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            time.sleep(delay)
