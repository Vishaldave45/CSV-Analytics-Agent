"""Unit tests for content hashing utilities."""

from __future__ import annotations

import hashlib

from csv_analytics_agent.persistence.hashing import compute_content_hash


def test_compute_content_hash_matches_sha256() -> None:
    content = b"col1,col2\n1,2\n3,4\n"
    expected = hashlib.sha256(content).hexdigest()
    assert compute_content_hash(content) == expected
    assert len(compute_content_hash(content)) == 64


def test_compute_content_hash_idempotent() -> None:
    content = b"test,data\n10,20\n"
    hash1 = compute_content_hash(content)
    hash2 = compute_content_hash(content)
    assert hash1 == hash2


def test_compute_content_hash_distinct_for_different_bytes() -> None:
    data_a = b"user_id,score\n1,100\n"
    data_b = b"user_id,score\n1,101\n"
    assert compute_content_hash(data_a) != compute_content_hash(data_b)


def test_compute_content_hash_empty_bytes() -> None:
    empty_hash = compute_content_hash(b"")
    assert empty_hash == hashlib.sha256(b"").hexdigest()
