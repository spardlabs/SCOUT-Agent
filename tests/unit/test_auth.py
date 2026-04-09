"""Tests for auth utilities."""

from scout.core.auth import generate_api_key, hash_api_key


class TestAuth:
    def test_generate_api_key_format(self):
        key = generate_api_key()
        assert key.startswith("sk_scout_")
        assert len(key) > 20

    def test_generate_api_key_unique(self):
        keys = {generate_api_key() for _ in range(10)}
        assert len(keys) == 10  # All unique

    def test_hash_api_key_deterministic(self):
        key = "sk_scout_test123"
        h1 = hash_api_key(key)
        h2 = hash_api_key(key)
        assert h1 == h2

    def test_hash_api_key_different_keys(self):
        h1 = hash_api_key("key-a")
        h2 = hash_api_key("key-b")
        assert h1 != h2

    def test_hash_api_key_length(self):
        h = hash_api_key("test")
        assert len(h) == 64  # SHA256 hex digest
