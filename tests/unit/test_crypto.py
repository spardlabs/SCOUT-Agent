"""Tests for crypto service (token encryption/decryption)."""

from scout.services.crypto import decrypt_token, encrypt_token


class TestCryptoService:
    def test_encrypt_decrypt_roundtrip(self):
        original = "sk-ant-api-key-12345"
        encrypted = encrypt_token(original)
        decrypted = decrypt_token(encrypted)
        assert decrypted == original

    def test_encrypted_differs_from_original(self):
        original = "my-secret-token"
        encrypted = encrypt_token(original)
        assert encrypted != original

    def test_different_inputs_produce_different_outputs(self):
        a = encrypt_token("token-a")
        b = encrypt_token("token-b")
        assert a != b

    def test_empty_string_roundtrip(self):
        encrypted = encrypt_token("")
        assert decrypt_token(encrypted) == ""
