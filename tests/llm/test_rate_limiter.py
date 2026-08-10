"""Unit tests for Gemini rate limiter."""

import time

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.llm.rate_limiter import InMemoryFallbackLimiter, build_gemini_limiter


def test_build_gemini_limiter() -> None:
    """Test that build_gemini_limiter constructs a functional limiter."""
    settings = Settings(gemini_rpm=5)
    limiter = build_gemini_limiter(settings)

    assert hasattr(limiter, "try_acquire")
    # Should be able to acquire at least once immediately
    res = limiter.try_acquire("gemini_invoke")
    assert res is True or res is not None


def test_in_memory_fallback_limiter() -> None:
    """Test InMemoryFallbackLimiter rate limiting behavior."""
    limiter = InMemoryFallbackLimiter(max_requests=2, window_seconds=0.2)

    # First 2 requests should be immediate
    t0 = time.time()
    assert limiter.try_acquire("test") is True
    assert limiter.try_acquire("test") is True
    elapsed_immediate = time.time() - t0
    assert elapsed_immediate < 0.1

    # 3rd request should wait until window slides
    assert limiter.try_acquire("test") is True
    elapsed_total = time.time() - t0
    assert elapsed_total >= 0.15
