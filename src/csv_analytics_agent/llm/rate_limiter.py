"""Process-local rate limiter guarding Gemini free-tier RPM budget."""

from __future__ import annotations

import time
from typing import Any

from csv_analytics_agent.config.setting import Settings

try:
    from pyrate_limiter import Duration, Limiter, Rate  # pyright: ignore[reportMissingImports]

    _PYRATE_LIMITER_AVAILABLE = True
except ModuleNotFoundError:
    _PYRATE_LIMITER_AVAILABLE = False


class InMemoryFallbackLimiter:
    """Sliding window in-memory rate limiter fallback when pyrate-limiter is absent."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []

    def try_acquire(self, name: str = "default") -> bool:
        """Attempt to acquire permission to execute a request.

        Blocks or cleans up expired timestamps and records the current request.
        """
        now = time.time()
        # Clean timestamps older than window
        self._timestamps = [t for t in self._timestamps if now - t < self.window_seconds]

        if len(self._timestamps) >= self.max_requests:
            # Need to wait until the oldest timestamp falls outside the window
            sleep_time = self.window_seconds - (now - self._timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < self.window_seconds]

        self._timestamps.append(time.time())
        return True


def build_gemini_limiter(settings: Settings) -> Any:
    """Build a process-local rate limiter based on settings.gemini_rpm.

    Args:
        settings: Application Settings containing gemini_rpm limit.

    Returns:
        pyrate_limiter.Limiter instance or InMemoryFallbackLimiter.
    """
    if _PYRATE_LIMITER_AVAILABLE:
        rate = Rate(settings.gemini_rpm, Duration.MINUTE)
        return Limiter(rate)
    return InMemoryFallbackLimiter(max_requests=settings.gemini_rpm, window_seconds=60.0)


__all__ = ["InMemoryFallbackLimiter", "build_gemini_limiter"]
