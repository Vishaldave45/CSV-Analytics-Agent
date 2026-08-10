"""Content hashing utilities for dataset caching and session identification."""

from __future__ import annotations

import hashlib


def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hex digest of raw file bytes.

    Used as the dataset cache key and stable session identifier.

    Args:
        content: Raw bytes of the uploaded file.

    Returns:
        64-character SHA-256 hexadecimal digest string.
    """
    return hashlib.sha256(content).hexdigest()
